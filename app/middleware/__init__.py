import copy
import logging
from datetime import datetime, timezone
from urllib.parse import quote

import falcon
import uuid
from confluent_kafka import Producer, KafkaError, KafkaException

# from app.tasks.main import producer_async
# from app.events.publishers.publisher import producer_async

import app.util.json as json
from app.config import settings
from app.da import GroupDA
from app.da.member import MemberNotificationsSettingDA
from app.exceptions.session import InvalidSessionError
from app.util.error import HTTPError
from app.util.session import get_session_cookie, validate_session
from app.da.activity import ActivityDA

import copyreg
from cgi import FieldStorage
from falcon_multipart.parser import Parser


logger = logging.getLogger(__name__)
logger_kafka = logging.getLogger(f"{__name__}_kafka")
logger_kafka.setLevel(logging.ERROR)

# Topic route table based on resource and method.
# TODO move this to env file or vyper
# TODO add event type to resource dict as well

ignore_routes = ['/healthz', '/healthz/headers']


def pickle_field_storage(c):
    logger.debug(f"Pickling copy of {type(c)} ")
    return "<byte-data>"


copyreg.pickle(FieldStorage, pickle_field_storage)
copyreg.pickle(Parser, pickle_field_storage)



class HandleForwardSlashMiddleware(object):
    def process_request(self, req, resp):
        # This allows to have `/` inside of the `file_path` field name
        logger.debug(f'request.path: {req.path}')
        if req.path.startswith("/member/file"):
            file_path = req.path[13:]
            logger.debug(f"quoting: {file_path}")
            file_path = quote(file_path, safe='')
            logger.debug(f"quoted: {file_path}")
            logger.debug(f"rewrite: /member/file/{file_path}")
            req.path = f"/member/file/{file_path}"


class CrossDomain(object):
    def process_response(self, req, resp, resource, req_succeeded):
        logger.debug(f'req.path: {req.path}')
        if req.path in ignore_routes:
            # logger.debug(f"Ignoring route: {req.path}")
            resp.complete = True
            return

        access_control_allow_origin = settings.get(
            "ACCESS_CONTROL_ALLOW_ORIGIN")
        access_control_allow_methods = settings.get(
            "ACCESS_CONTROL_ALLOW_METHODS")
        access_control_allow_credentials = settings.get(
            "ACCESS_CONTROL_ALLOW_CREDENTIALS")
        access_control_allow_headers = settings.get(
            "ACCESS_CONTROL_ALLOW_HEADERS")

        # logger.debug("ACCESS_CONTROL_ALLOW_ORIGIN: {}".format(
        #     access_control_allow_origin))
        # logger.debug("ACCESS_CONTROL_ALLOW_METHODS: {}".format(
        #     access_control_allow_methods))
        # logger.debug("ACCESS_CONTROL_ALLOW_CREDENTIALS: {}".format(
        #     access_control_allow_credentials))
        # logger.debug("ACCESS_CONTROL_ALLOW_HEADERS: {}".format(
        #     access_control_allow_headers))

        # This section here overrides the `access-control-allow-origin`
        # to be dynamic, this means that if the requests come from any
        # domains defined in web.domains, then we allow the origin
        # TODO: Remove this logic
        # request_domain is the domain being used by the original requester
        # we use forwarded_host because these API calls will be proxied in by
        # a load balancer like AWS ELB or NGINX, thus we need to know how
        # this is being requested as:
        #  (e.g. https://ameraiot.com/api/valid-session)
        request_domain = req.env.get('HTTP_ORIGIN', req.forwarded_host)

        # default_domain is the domain as configured in the [web] part of the
        # this domain is the expected domain the application will run in
        # where SSL is terminated, before requests are proxied
        # to the application
        default_domain = settings.get('web.domain')

        # logger.debug("SETTINGS Domain: {}".format(default_domain))
        # logger.debug("REQUEST Forwarded Host: {}".format(request_domain))
        # logger.debug("REQUEST Host: {}".format(req.host))
        # logger.debug("REQUEST Access Route: {}".format(req.access_route))
        # logger.debug("REQUEST Netloc: {}".format(req.netloc))
        # logger.debug("REQUEST Port: {}".format(req.port))
        # logger.debug("ENV: {}".format(pformat(req.env)))

        if access_control_allow_origin == "auto":
            domains = settings.get("web.domains")
            # logger.debug("REQUEST_DOMAIN: {}".format(request_domain))
            # logger.debug("ALLOWED_DOMAINS: {}".format(pformat(domains)))
            domains = [d for d in domains if d in request_domain]
            # logger.debug("DOMAINS FOUND: {}".format(domains))
            if len(domains) == 0:
                access_control_allow_origin = default_domain
            else:
                access_control_allow_origin = request_domain
            # logger.debug("OVERRIDE_ACCESS_CONTROL_ALLOW_ORIGIN: {}".format(
            #     access_control_allow_origin))

        resp.set_header("Access-Control-Allow-Origin",
                        access_control_allow_origin)
        resp.set_header("Access-Control-Allow-Methods",
                        access_control_allow_methods)
        resp.set_header("Access-Control-Allow-Credentials",
                        access_control_allow_credentials)
        resp.set_header("Access-Control-Allow-Headers",
                        access_control_allow_headers)


class JSONTranslator(object):
    def process_request(self, req, resp):
        if req.content_length in (None, 0):
            return

        body = req.stream.read()
        if not body:
            raise HTTPError(400, "A valid JSON document is required.")

        try:
            req.context["doc"] = json.loads(body.decode("utf-8"))

        except (ValueError, UnicodeDecodeError):
            raise HTTPError(400, "Could not decode the request body. The "
                                 "JSON was incorrect or not encoded as "
                                 "UTF-8.")

    def process_response(self, req, resp, resource, req_succeeded):
        if "result" not in req.context:
            return

        resp.body = json.dumps(req.context["result"])


class TopicData(object):
    """ Model for topic data for kafka and activity query"""

    def __init__(self):
        self.event_key = ""
        self.headers = {}
        self.req_params = {}
        self.req_url_params = {}
        self.req_data = {}
        self.resp_data = {}
        self.http_status = 0
        self.session_key = ""
        self.session_data = {}
        self.member_id = ""
        self.event_type = ""
        self.status = "started"
        self.create_date = ""
        self.referer_url = ""
        self.url = ""


class KafkaProducerMiddleware(object):

    def __handle_kafka_errors(self, err):
        # https://docs.confluent.io/3.0.0/clients/confluent-kafka-python/index.html#kafkaerror
        # KafkaError{code=_TRANSPORT,val=-195,str="kafka:9092/bootstrap:
        #   Connect to ipv4#23.202.231.169:9092 failed:
        #   Connection refused (after 50ms in state CONNECT)"}
        # KafkaError{code=_ALL_BROKERS_DOWN,val=-187,
        #   str="1/1 brokers are down"}
        logger_kafka.error(f"Kafka Error: {err}")
        if err.name() in ['_ALL_BROKERS_DOWN', '_TRANSPORT']:
            self.producer_connected = False
            self.p.abort_transaction()
            logger_kafka.error(f"Kafka Connection issue: {err}")

    def __init__(self):

        producer_conf = {
            'bootstrap.servers': settings.get('kafka.bootstrap_servers')
        }

        if settings.get('kafka.sasl.username'):
            producer_conf.update({
                'sasl.mechanisms': settings.get('kafka.sasl.mechanisms'),
                'security.protocol': settings.get('kafka.security.protocol'),
                'sasl.username': settings.get('kafka.sasl.username'),
                'sasl.password': settings.get('kafka.sasl.password'),
            })
        if settings.get('ENV_NAME') == 'LOCAL':
            producer_conf['error_cb'] = self.__handle_kafka_errors

        self.topic = None
        self.session_id = ""
        self.session_data = ""
        self.member_id = ""
        self.u = ""
        self.topic_data = TopicData()
        self.db_query_data = {}
        try:
            self.p = Producer(producer_conf, logger=logger_kafka)
            self.producer_connected = True
        except KafkaException as e:
            logger_kafka.debug(f"KafkaException: {e}")
            self.__handle_kafka_errors(e.args[0])

        # self.p = Producer({
        #     'bootstrap.servers': 'kafka:9092'
        # })

    def process_request(self, req, resp):
        if req.path in ignore_routes:
            # logger_kafka.debug(f"Ignoring route: {req.path}")
            return

    def process_resource(self, req, resp, resource, params):
        if req.path in ignore_routes:
            # logger_kafka.debug(f"Ignoring route: {req.path}")
            return

        topic_data = TopicData()
        db_query_data = {}

        # If no specific topic necessary.
        # Send all other data to activity topic for monitoring purposes
        topic = "activity"
        topic_data.event_type = "activity"

        try:
            topic, event = self._resource_topic_event(req, resource)
            topic_data.event_type = event
        except Exception as e:
            logger_kafka.debug(f"""
                Failed to retrieve topic from: {resource.__class__.__name__}
                Request Method: {req.method}
                Template: {req.uri_template}
                Path: {req.path}
            """)
            logger_kafka.exception(
                f'Failed to retrieve topic from: {resource.__class__.__name__}')
            logger_kafka.error(e)

            pass

        try:
            # Get member and session data
            session_key = get_session_cookie(req)
            try:
                topic_data.session_key = session_key
                topic_data.session_data = validate_session(
                    session_key, full=True)
                topic_data.member_id = topic_data.session_data["member_id"]
            except InvalidSessionError:
                topic_data.session_data = {}
                topic_data.member_id = None

            body = None
            if req.content_type == falcon.MEDIA_JSON:
                body = req.media
            u = str(uuid.uuid4())
            # Set event_key on headers so we can  link req/resp
            req.headers['event_key'] = u
            req.headers['req_url_params'] = self._sanitize(params)
            topic_data.status = 'started'
            topic_data.event_key = u
            topic_data.headers = req.headers
            topic_data.req_params = req.params
            topic_data.req_url_params = params
            topic_data.req_data = body
            topic_data.headers = self._sanitize(req.headers)
            topic_data.req_params = self._sanitize(req.params)
            topic_data.req_url_params = self._sanitize(params)
            topic_data.req_data = self._sanitize(body)
            topic_data.resp_data = None
            topic_data.create_date = datetime.now(timezone.utc)
            topic_data.referer_url = req.headers.get('REFERER')
            topic_data.url = req.url

            # Gevent to not block request. Create dict from topic_data model for kafka
            topic_data_dict = vars(topic_data)
            self.producer_async(topic, [json.dumps(topic_data_dict,
                                                   default_parser=json.parser)])

            # Write activity to db - copy topic data to preserve json
            db_query_data = copy.deepcopy(topic_data_dict)
            db_query_data['topic'] = topic
            db_query_data['headers'] = json.dumps(
                topic_data.headers, default_parser=json.parser)
            db_query_data["req_params"] = json.dumps(
                topic_data.req_params, default_parser=json.parser)
            db_query_data["req_url_params"] = json.dumps(topic_data.req_url_params,
                                                         default_parser=json.parser)
            db_query_data["req_data"] = json.dumps(
                topic_data.req_data, default_parser=json.parser)
            db_query_data["resp_data"] = json.dumps(
                topic_data.resp_data, default_parser=json.parser)
            db_query_data["session_data"] = json.dumps(topic_data.session_data,
                                                       default_parser=json.parser)

            ActivityDA.insert_activity(**db_query_data)
        except Exception as e:
            logger_kafka.error(e, exc_info=True)

        return

    def process_response(self, req, resp, resource, req_succeeded):
        if req.path in ignore_routes:
            # logger_kafka.debug(f"Ignoring route: {req.path}")
            return

        topic_data = TopicData()
        db_query_data = {}

        # If no specific topic necessary.
        # Send all other data to activity topic for monitoring purposes
        topic = "activity"
        topic_data.event_type = "activity"


        try:
            topic, event = self._resource_topic_event(req, resource)
            topic_data.event_type = event
        except Exception as e:
            logger_kafka.debug(f"""
                Failed to retrieve topic from: {resource.__class__.__name__}
                Request Method: {req.method}
                Template: {req.uri_template}
                Path: {req.path}
            """)
            logger_kafka.exception(
                f'Failed to retrieve topic from: {resource.__class__.__name__}')
            logger_kafka.error(e)

            pass

        try:
            session_key = get_session_cookie(req)
            try:
                topic_data.session_key = session_key
                topic_data.session_data = validate_session(
                    session_key, full=True)
                topic_data.member_id = topic_data.session_data["member_id"]
            except InvalidSessionError:
                topic_data.session_data = {}
                topic_data.member_id = None

            body = None
            if req.content_type == falcon.MEDIA_JSON:
                body = req.media
            u = req.headers.get('event_key')
            topic_data.status = 'ended'
            topic_data.event_key = u
            topic_data.headers = req.headers
            topic_data.req_params = req.params
            topic_data.req_url_params = req.headers.get('req_url_params')
            topic_data.req_data = body
            topic_data.headers = self._sanitize(req.headers)
            topic_data.req_params = self._sanitize(req.params)
            # topic_data.req_url_params = self._sanitize(params)
            topic_data.req_data = self._sanitize(body)
            topic_data.create_date = datetime.now(timezone.utc)
            topic_data.referer_url = req.headers.get('REFERER')
            topic_data.url = req.url

            body = None
            try:
                body = json.loads(resp.body)
            except Exception as e:
                # Response is non json, do nothing
                pass

            topic_data.resp_data = body
            topic_data.http_status = resp.status

            # Gevent to not block request. Create dict from topic_data model for kafka
            topic_data_dict = vars(topic_data)

            self.producer_async(topic, [json.dumps(topic_data_dict,
                                                   default_parser=json.parser)])

            # Write activity to db - copy topic data to preserve json
            db_query_data = copy.deepcopy(topic_data_dict)
            db_query_data['topic'] = topic
            db_query_data['headers'] = json.dumps(
                topic_data.headers, default_parser=json.parser)
            db_query_data["req_params"] = json.dumps(
                topic_data.req_params, default_parser=json.parser)
            db_query_data["req_url_params"] = json.dumps(topic_data.req_url_params,
                                                         default_parser=json.parser)
            db_query_data["req_data"] = json.dumps(
                topic_data.req_data, default_parser=json.parser)
            db_query_data["resp_data"] = json.dumps(
                topic_data.resp_data, default_parser=json.parser)
            db_query_data["session_data"] = json.dumps(topic_data.session_data,
                                                       default_parser=json.parser)

            ActivityDA.insert_activity(**db_query_data)

            # Check if event maps to a notification type
            # TODO Member_ID for notifications should be from the payload since the request came from the sender
            event_type_to_notification = {
                settings.get('kafka.event_types.post.group_crud'): "RequestToJoinGroup",
                settings.get('kafka.event_types.put.group_membership_response'): "GroupJoin",
                settings.get('kafka.event_types.post.create_contact'): "RequestContact",
                settings.get('kafka.event_types.put.contact_request_response'): "Contact",
                settings.get('kafka.event_types.post.mail_draft_send'): "AmeraMail",
                }
            if 200 <= int(topic_data.http_status[:3]) < 300:
                # Check if event_type matches a notification
                notification_type = event_type_to_notification.get(topic_data.event_type)
                logger_kafka.debug(f"### {topic_data.event_type}")
                if notification_type:
                    notification_sent = False
                    member_id = None
                    if notification_type == "AmeraMail":
                        pass
                        # TODO How to get member_id for TO. Query mail object based on Member and mail_id
                        #  from req_url_params
                        # member_id = BaseMailDA.get_mail_detail(topic_data.req_url_params.get('member'))
                    elif notification_type == "RequestToJoinGroup":
                        logger_kafka.debug("RequestTOJoinGroup Notification")
                        member_id = req.headers.get('kafka_invitee_id')
                        topic_data_dict['kafka_invitee_id'] = member_id
                        topic_data_dict['kafka_group_name'] = req.headers.get('kafka_group_name')
                        # req.set_header('kafka_member_id', "")
                    elif notification_type == "GroupJoin":
                        # TODO revert header. Do it efficiently
                        # req.header('group_id', "")
                        group = GroupDA.get_group(int(req.headers.get('kafka_group_id')))
                        member_id = group.get('group_leader_id')
                        topic_data_dict['kafka_group_name'] = group.get('name')
                        topic_data_dict['kafka_group_leader_id'] = group.get('group_leader_id')
                        # topic_data_dict['kafka_group_id'] = req.headers.get('kafka_group_id')
                        topic_data_dict['kafka_group_status'] = req.headers.get('kafka_group_status')
                    elif notification_type == "RequestContact":
                        logger_kafka.debug(" REQUEST CONTACT")
                        contact_list = req.headers.get('kafka_contact_id_list')
                        # req.set_header('kafka_contact_member_id_list', "")
                        if contact_list:
                            logger_kafka.debug(f"### {contact_list}")
                            topic_data_dict['kafka_contact_id_list'] = json.loads(contact_list)
                            self.producer_async("sms", [json.dumps(topic_data_dict,
                                                                   default_parser=json.parser)])
                            self.producer_async("email", [json.dumps(topic_data_dict,
                                                                   default_parser=json.parser)])
                        notification_sent = True
                    elif notification_type == "Contact":
                        member_id = int(req.headers.get('kafka_contacter_id'))
                        topic_data_dict['kafka_contacter_id'] = member_id
                        topic_data_dict['kafka_contact_request_status'] = req.headers.get('kafka_contact_request_status')
                        # req.set_header('kafka_contact_accepted_id', "")

                    # produce notification if not already sent
                    if member_id and not notification_sent:
                        self.produce_notification(member_id, notification_type, topic_data_dict)

        except Exception as e:
            logger_kafka.error(e, exc_info=True)

        return

    def producer_async(self, topic, data_source):
        # create_topic(self.topic)
        if 'meinheld' in settings.get('WORKER_CLASS'):
            return

        for data in data_source:
            try:
                # Poll will trigger the callback self.deliver_report which indicates if the message has
                # successfully been delivered. Not sure if this means a consumer has read it or its been successfully
                # been delivered to a client

                self.p.poll(0)
                # Asynchronously produce a message, the delivery report callback
                # will be triggered from poll() above, or flush() below, when the message has
                # been successfully delivered or failed permanently.
                data = data.encode('utf-8')
                logger_kafka.debug(f"PRODUCING to {topic} {data}")
                self.p.produce(topic, value=data, callback=self.delivery_report)
            except KafkaException as exc:
                logger_kafka.error('KafkaException When Producing or Polling')
                self.__handle_kafka_errors(exc.args[0])
            except KafkaError as exc:
                logger_kafka.error('KafkaError When Producing or Polling')
                self.__handle_kafka_errors(exc)
            except Exception as exc:
                logger_kafka.exception(exc, exc_info=True)

        # Wait for any outstanding messages to be delivered and delivery report
        # callbacks to be triggered.
        if self.producer_connected:
            self.p.flush()

    @staticmethod
    def _sanitize(data):
        if not data:
            return data

        data = data.copy()  # Copying to not modify the original data for the resources
        for key in data.keys():
            if 'password' in key:
                data[key] = '**********'
        return data

    @staticmethod
    def _resource_topic_event(req, resource):
        logger_kafka.debug(f"Attempt to get route method: {req.method}")
        # Get kafka data from resource for  topic routing and event_type
        if not hasattr(resource, "kafka_data"):
            raise KeyError("No need to go further, no kafka_data")

        method_map = resource.kafka_data.get(req.method)

        try:
            uri_map = method_map["uri"]
            logger_kafka.debug(f"""
            Attempt to get
                URI event: {uri_map}
                FROM: {req.uri_template}
                OR: {req.path}
            """)
            try:
                method_map = uri_map[req.uri_template]
            except KeyError:
                method_map = uri_map[req.path]
        except TypeError:
            pass
        except KeyError:
            pass

        topic = method_map["topic"]
        event = method_map["event_type"]

        if not topic:
            raise KeyError(f"Topic is: {topic} which is invalid - KeyError")

        logger_kafka.debug(
            f"TOPIC AND EVENT_TYPE FOUND: {topic}, {event}")
        return topic, event

    @staticmethod
    def delivery_report(err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            logger_kafka.debug('Message delivery failed: {}'.format(err))
        else:
            logger_kafka.debug('Message delivered to {} [{}] {}'.format(
                msg.topic(), msg.partition(), msg.value()))

    def produce_notification(self, member_id, notification_type, topic_data_dict):
        member_notificiation_settings = MemberNotificationsSettingDA.get_notifications_setting(
            memberId=int(member_id)).get('data')
        if member_notificiation_settings:
            sms_topic = member_notificiation_settings.get('sms').get(notification_type)
            email_topic = member_notificiation_settings.get('email').get(notification_type)
        # TODO Group these together into one json for kafka.
            if sms_topic:
                self.producer_async('sms', [json.dumps(topic_data_dict,
                                                       default_parser=json.parser)])
            if email_topic:
                self.producer_async('email', [json.dumps(topic_data_dict,
                                                         default_parser=json.parser)])
        else:
            logger_kafka.error("No notificaiton settings for user")

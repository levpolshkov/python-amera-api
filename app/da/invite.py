import logging
from datetime import datetime

from app.util.db import source
from app.exceptions.data import DuplicateKeyError, DataMissingError, \
    RelationshipReferenceError
from app.exceptions.invite import InviteExistsError, InviteDataMissingError, \
    InviteInvalidInviterError
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class InviteDA(object):
    source = source

    @classmethod
    def create_invite(cls, invite_key, email, first_name, last_name,
                      inviter_member_id, expiration, commit=True):

        query = ("""
        INSERT INTO invite
            (invite_key, email, first_name, last_name,
                inviter_member_id, expiration)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """)

        params = (
            invite_key, email, first_name, last_name,
            inviter_member_id, expiration
        )
        try:
            cls.source.execute(query, params)
            invite_id = cls.source.get_last_row_id()

            if commit:
                cls.source.commit()

            return invite_id
        except DuplicateKeyError as err:
            raise InviteExistsError from err
        except DataMissingError as err:
            raise InviteDataMissingError from err
        except RelationshipReferenceError as err:
            raise InviteInvalidInviterError from err

    @classmethod
    def get_invite(cls, invite_key):
        query = ("""
        SELECT
            id, invite_key, email, role_id, group_id, expiration,
            first_name, last_name, inviter_member_id,
            country_code, phone_number, registered_member_id
        FROM invite
        WHERE invite_key = %s
        """)

        params = (invite_key,)
        cls.source.execute(query, params)
        if cls.source.has_results():
            (
                id, invite_key, email,
                role_id, group_id, expiration, first_name,
                last_name, inviter_member_id,
                country, phone_number, registered_member_id
            ) = cls.source.cursor.fetchone()
            invite = {
                "id": id,
                "invite_key": invite_key,
                "email": email,
                "role_id": role_id,
                "group_id": group_id,
                "expiration": expiration,
                "first_name": first_name,
                "last_name": last_name,
                "inviter_member_id": inviter_member_id,
                "country": country,
                "phone_number": phone_number,
                "registered_member_id": registered_member_id
            }
            return invite

        return None

    @classmethod
    def get_invite_for_register(cls, invite_key):
        query = ("""
        SELECT
            id, invite_key, email, group_id, expiration,
            first_name, last_name, country_code, phone_number, registered_member_id, confirm_phone_required
        FROM invite
        WHERE invite_key = %s
        """)

        params = (invite_key,)
        cls.source.execute(query, params)
        if cls.source.has_results():
            (
                id, invite_key, email, group_id, expiration,
                first_name, last_name, country, phone_number, registered_member_id, confirm_phone_required
            ) = cls.source.cursor.fetchone()
            invite = {
                "id": id,
                "invite_key": invite_key,
                "email": email,
                "group_id": group_id,
                "expiration": expiration,
                "first_name": first_name,
                "last_name": last_name,
                "country": country,
                "phone_number": phone_number,
                "registered_member_id": registered_member_id,
                "confirm_phone_required": confirm_phone_required
            }
            return invite

        return None

    @classmethod
    def update_invite_registered_member(cls, invite_key, registered_member_id, commit=True):

        query = ("""
        UPDATE invite SET
            registered_member_id = %s
        WHERE invite_key = %s
        """)

        params = (
            registered_member_id, invite_key,
        )
        try:
            cls.source.execute(query, params)

            if commit:
                cls.source.commit()
        except DataMissingError as err:
            raise InviteDataMissingError from err
        except RelationshipReferenceError as err:
            raise InviteInvalidInviterError from err

    @classmethod
    def delete_invite(cls, invite_key, commit=True):
        query = ("""
        DELETE FROM invite WHERE invite_key = %s
        """)

        params = (invite_key)
        res = cls.source.execute(query, params)
        if commit:
            cls.source.commit()

        return res

    @classmethod
    def change_invite(cls, id):
        query = (f""" 
        UPDATE invite SET expiration = '{datetime.now() + relativedelta(months=+1)}' 
        WHERE invite.id = %s;
        """)
        params = (id)
        cls.source.execute(query, params)
        cls.source.commit()

    @classmethod
    def get_invites(cls, search_key, page_size=None, page_number=None, sort_params='', get_all=False, member_id=None):
        sort_columns_string = 'invite.first_name ASC, invite.last_name ASC'
        if sort_params:
            invite_dict = {
                'id': 'invite.id',
                'invite_key': 'invite.invite_key',
                'email': 'invite.email',
                'expiration': 'invite.expiration',
                'first_name': 'invite.first_name',
                'last_name': 'invite.last_name',
                'inviter_member_id': 'invite.inviter_member_id',
                'status': 'invite.registered_member_id',
                'date_invited': 'invite.create_date',
                'update_date': 'invite.update_date',
                'inviter_first_name': 'member.first_name',
                'inviter_last_name': 'member.last_name',
                'inviter_email': 'member.email',
                'company_name': 'registered_member.company_name',
                'group_id': 'member_group.id',
                'group_name': 'member_group.group_name',
                'date_registered': 'registered_member.create_date',
                'city': 'remote_city_name',
                'ip_address': 'remote_ip_address',
                'region': 'remote_region_name',
                'country': ' remote_country_name'
            }
            sort_columns_string = formatSortingParams(
                sort_params, invite_dict) or sort_columns_string

        query = (f"""
        SELECT 
            invite.id,
            invite.invite_key,
            invite.email,
            invite.expiration,
            invite.first_name,
            invite.last_name,
            invite.inviter_member_id,
            invite.registered_member_id,
            invite.create_date,
            invite.update_date,
            member.first_name,
            member.last_name,
            member.email,
            registered_member.company_name,
            member_group.id,
            member_group.group_name,
            registered_member.create_date as registered_date,
            member_location.city AS remote_city_name,
            CASE WHEN member_location.province IS NOT NULL THEN member_location.province ELSE member_location.state END as remote_region_name,
            member_location.country AS remote_country_name
        FROM invite
            LEFT JOIN member on invite.inviter_member_id = member.id
            LEFT OUTER JOIN member_group on invite.group_id = member_group.id
            LEFT OUTER JOIN member AS registered_member on invite.registered_member_id = registered_member.id
            LEFT OUTER JOIN member_location on member_location.member_id = registered_member.id AND member_location.location_type = 'home'
        WHERE 
            {f'inviter_member_id = {member_id} AND' if not get_all else ''}
            ( invite.email LIKE %s
            OR invite.first_name LIKE %s
            OR invite.last_name LIKE %s
            OR member.first_name LIKE %s
            OR member.last_name LIKE %s
            OR member.email LIKE %s
            OR member_group.group_name LIKE %s )
        ORDER BY {sort_columns_string}
        """)

        countQuery = (f"""
        SELECT
            COUNT(*)
        FROM invite
        LEFT JOIN member on invite.inviter_member_id = member.id
        LEFT OUTER JOIN member_group on invite.group_id = member_group.id
        WHERE 
            {f'inviter_member_id = {member_id} AND' if not get_all else ''}
            ( invite.email LIKE %s
            OR invite.first_name LIKE %s
            OR invite.last_name LIKE %s
            OR member.first_name LIKE %s
            OR member.last_name LIKE %s
            OR member.email LIKE %s
            OR member_group.group_name LIKE %s )
        """)

        like_search_key = """%{}%""".format(search_key)
        params = tuple(7 * [like_search_key])

        cls.source.execute(countQuery, params)

        count = 0
        if cls.source.has_results():
            (count,) = cls.source.cursor.fetchone()

        if page_size and page_number:
            query += """LIMIT %s OFFSET %s"""
            offset = 0
            if page_number > 0:
                offset = page_number * page_size
            params = params + (page_size, offset)

        invites = []

        cls.source.execute(query, params)
        if cls.source.has_results():
            for (
                    id,
                    invite_key,
                    email,
                    expiration,
                    first_name,
                    last_name,
                    inviter_member_id,
                    registered_member_id,
                    create_date,
                    update_date,
                    inviter_first_name,
                    inviter_last_name,
                    inviter_email,
                    company_name,
                    group_id,
                    group_name,
                    registered_date,
                    remote_city_name,
                    remote_region_name,
                    remote_country_name
            ) in cls.source.cursor:
                invite = {
                    "id": id,
                    "invite_key": invite_key,
                    "email": email,
                    "expiration": expiration,
                    "first_name": first_name,
                    "last_name": last_name,
                    "inviter_member_id": inviter_member_id,
                    "registered_member_id": registered_member_id,
                    "status": "Registered" if registered_member_id else "Unregistered",
                    "create_date": create_date,
                    "update_date": update_date,
                    "inviter_first_name": inviter_first_name,
                    "inviter_last_name": inviter_last_name,
                    "inviter_email": inviter_email,
                    "group_id": group_id,
                    "group_name": group_name,
                    "registered_date": registered_date,
                    "city":  remote_city_name,
                    "company_name": company_name,
                    "region": remote_region_name,
                    "country": remote_country_name
                }
                invites.append(invite)

        return {"activities": invites, "count": count}


def formatSortingParams(sort_by, entity_dict):
    columns_list = sort_by.split(',')
    new_columns_list = list()

    for column in columns_list:
        if column[0] == '-':
            column = column[1:]
            column = entity_dict.get(column)
            if column:
                column = column + ' DESC'
                new_columns_list.append(column)
        else:
            column = entity_dict.get(column)
            if column:
                column = column + ' ASC'
                new_columns_list.append(column)

    return (',').join(column for column in new_columns_list)


-- ------------------------------------------------------------------------------
-- Table:        timezone
-- Description:  contains timezone UTC and DST offsets
-- ------------------------------------------------------------------------------

CREATE TABLE timezone (

  id                    SERIAL          PRIMARY KEY,
  utc_offset            INTERVAL        NOT NULL,
  dst_offset            INTERVAL        NOT NULL,
  name                  VARCHAR(64)     NOT NULL,
  country_code_id       INTEGER 

);
CREATE INDEX timezone_country_code_id_idx ON timezone (country_code_id);

-- ------------------------------------------------------------------------------
-- Load Data:    timezone
-- Description:  list of timezone UTC and DST offsets
-- ------------------------------------------------------------------------------

INSERT INTO timezone (utc_offset, dst_offset, name, country_code_id)

  VALUES    ( '-11:00', '-11:00', 'Midway Islands',             16 ),
            ( '-11:00', '-11:00', 'Pago Pago',                  16 ),
            ( '-10:00', '-10:00', 'Hawaii',                    840 ),
            ( '-9:00',  '-8:00',  'Alaska',                    840 ),
            ( '-8:00',  '-7:00',  'Pacific Time (USA)',        840 ),
            ( '-8:00',  '-7:00',  'Pacific Time (Canada)',     124 ),
            ( '-8:00',  '-7:00',  'Tijuana',                   484 ),
            ( '-7:00',  '-7:00',  'Arizona',                   840 ),
            ( '-7:00',  '-6:00',  'Mountain Time (USA)',       840 ),
            ( '-7:00',  '-6:00',  'Mountain Time (Canada)',    124 ),
            ( '-7:00',  '-6:00',  'Mazatlán',                  484 ),
            ( '-6:00',  '-6:00',  'Guatemala',                 320 ),
            ( '-6:00',  '-6:00',  'El Salvador',               222 ),
            ( '-6:00',  '-6:00',  'Managua',                   558 ),
            ( '-6:00',  '-6:00',  'Costa Rica',                188 ),
            ( '-6:00',  '-6:00',  'Tegucigalpa',               340 ),
            ( '-6:00',  '-6:00',  'Chihuahua',                 484 ),
            ( '-6:00',  '-5:00',  'Winnipeg',                  124 ),
            ( '-6:00',  '-5:00',  'Central Time (USA)',        840 ),
            ( '-6:00',  '-5:00',  'Central Time (Canada)',     124 ),
            ( '-6:00',  '-5:00',  'Mexico City',               484 ),
            ( '-5:00',  '-5:00',  'Panama',                    591 ),
            ( '-5:00',  '-5:00',  'Bogota',                    170 ),
            ( '-5:00',  '-5:00',  'Lima',                      604 ),
            ( '-5:00',  '-5:00',  'Monterrey',                 484 ),
            ( '-5:00',  '-4:00',  'Montreal',                  124 ),
            ( '-5:00',  '-4:00',  'Eastern Time (USA)',        840 ),
            ( '-5:00',  '-4:00',  'Eastern Time (Canada)',     124 ),
            ( '-4:00',  '-4:00',  'India (East)',              356 ),
            ( '-4:00',  '-4:00',  'Puerto Rico',               630 ),
            ( '-4:00',  '-4:00',  'Caracas',                   724 ),
            ( '-4:00',  '-3:00',  'Santiago',                  152 ),
            ( '-4:00',  '-4:00',  'La Paz',                     68 ),
            ( '-4:00',  '-4:00',  'Guyana',                    328 ),
            ( '-4:00',  '-3:00',  'Halifax',                   124 ),
            ( '-3:00',  '-3:00',  'Montevideo',                858 ),
            ( '-3:00',  '-3:00',  'Recife',                     76 ),
            ( '-3:00',  '-3:00',  'Buenos Aires',               32 ),
            ( '-3:00',  '-3:00',  'Georgetown',                328 ),
            ( '-3:00',  '-3:00',  'Sao Paulo',                  76 ),
            ( '-4:00',  '-3:00',  'Atlantic Time (Canada)',    124 ),
            ( '-3:30',  '-2:30',  'Newfoundland & Labrador',   124 ),
            ( '-3:00',  '-2:00',  'Greenland',                 304 ),
            ( '-1:00',  '-1:00',  'Cape Verde Islands',        132 ),
            ( '0:00',   '0:00',   'Azores',                    620 ),
            ( '0:00',   '0:00',   'Universal Time (UTC)',     NULL ),
            ( '0:00',   '0:00',   'Greenwich Mean Time (GMT)',NULL ),
            ( '0:00',   '0:00',   'Reykjavik',                 352 ),
            ( '0:00',   '0:00',   'Nouakchott',                478 ),
            ( '0:00',   '+1:00',  'Dublin',                    372 ),
            ( '0:00',   '+1:00',  'London',                    826 ),
            ( '+1:00',  '+1:00',  'Lisbon',                    380 ),
            ( '+1:00',  '+0:00',  'Casablanca',                504 ),
            ( '+1:00',  '+1:00',  'Central Africa',            140 ),
            ( '+1:00',  '+1:00',  'Algiers',                    12 ),
            ( '+1:00',  '+1:00',  'Tunis',                     788 ),
            ( '+1:00',  '+2:00',  'Belgrade',                  688 ),
            ( '+1:00',  '+2:00',  'Bratislava',                703 ),
            ( '+1:00',  '+2:00',  'Ljubljana',                 705 ),
            ( '+1:00',  '+2:00',  'Sarajevo',                   70 ),
            ( '+1:00',  '+2:00',  'Skopje',                    807 ),
            ( '+1:00',  '+2:00',  'Zagreb',                    191 ),
            ( '+1:00',  '+2:00',  'Oslo',                      578 ),
            ( '+1:00',  '+2:00',  'Copenhagen',                208 ),
            ( '+1:00',  '+2:00',  'Brussels',                   56 ),
            ( '+1:00',  '+2:00',  'Berlin',                    279 ),
            ( '+1:00',  '+2:00',  'Stockholm',                 752 ),
            ( '+1:00',  '+2:00',  'Amsterdam',                 528 ),
            ( '+1:00',  '+2:00',  'Rome',                      380 ),
            ( '+1:00',  '+2:00',  'Vienna',                     40 ),
            ( '+1:00',  '+2:00',  'Luxembourg',                442 ),
            ( '+1:00',  '+2:00',  'Paris',                     250 ),
            ( '+1:00',  '+2:00',  'Zurich',                    756 ),
            ( '+1:00',  '+2:00',  'Madrid',                    724 ),
            ( '+2:00',  '+2:00',  'Harare',                    716 ),
            ( '+2:00',  '+2:00',  'Pretoria',                  710 ),
            ( '+1:00',  '+2:00',  'Warsaw',                    616 ),
            ( '+1:00',  '+2:00',  'Prague',                    203 ),
            ( '+1:00',  '+2:00',  'Bratislava',                703 ),
            ( '+1:00',  '+2:00',  'Budapest',                  348 ),
            ( '+2:00',  '+2:00',  'Tripoli',                   343 ),
            ( '+2:00',  '+2:00',  'Cairo',                     818 ),
            ( '+2:00',  '+2:00',  'Johannesburg',              710 ),
            ( '+2:00',  '+2:00',  'Khartoum',                  729 ),
            ( '+3:00',  '+3:00',  'Helsinki',                  246 ),
            ( '+3:00',  '+3:00',  'Nairobi',                   404 ),
            ( '+3:00',  '+3:00',  'Sofia',                     643 ),
            ( '+3:00',  '+3:00',  'Istanbul',                  792 ),
            ( '+3:00',  '+3:00',  'Athens',                    300 ),
            ( '+3:00',  '+3:00',  'Bucharest',                 642 ),
            ( '+3:00',  '+3:00',  'Nicosia',                   196 ),
            ( '+3:00',  '+3:00',  'Beirut',                    422 ),
            ( '+3:00',  '+3:00',  'Damascus',                  760 ),
            ( '+3:00',  '+3:00',  'Jerusalem',                 376 ),
            ( '+3:00',  '+3:00',  'Amman',                     400 ),
            ( '+3:00',  '+3:00',  'Moscow',                    643 ),
            ( '+3:00',  '+3:00',  'Bagdad',                    368 ),
            ( '+3:00',  '+3:00',  'Kuwait',                    414 ),
            ( '+3:00',  '+3:00',  'Riyadh',                    682 ),
            ( '+3:00',  '+3:00',  'Bahrain',                    48 ),
            ( '+3:00',  '+3:00',  'Qatar',                     634 ),
            ( '+3:00',  '+3:00',  'Aden',                      887 ),
            ( '+3:00',  '+3:00',  'Djibouti',                  262 ),
            ( '+3:00',  '+3:00',  'Mogadishu',                 706 ),
            ( '+3:00',  '+3:00',  'Kiev',                      804 ),
            ( '+3:00',  '+3:00',  'Minsk',                     112 ),
            ( '+4:00',  '+4:00',  'Dubai',                     784 ),
            ( '+4:00',  '+4:00',  'Muscat',                    512 ),
            ( '+4:00',  '+4:00',  'Baku',                       31 ),
            ( '+4:00',  '+4:00',  'Tbilisi',                   268 ),
            ( '+4:00',  '+4:00',  'Yerevan',                    51 ),
            ( '+3:30',  '+4:30',  'Tehran',                    364 ),
            ( '+4:30',  '+4:30',  'Kabul',                       4 ),
            ( '+5:00',  '+5:00',  'Yekaterinburg',             643 ),
            ( '+5:00',  '+5:00',  'Islamabad',                 586 ),
            ( '+5:00',  '+5:00',  'Karachi',                   586 ),
            ( '+5:00',  '+5:00',  'Tashkent',                  860 ),
            ( '+5:30',  '+5:30',  'India',                     356 ),
            ( '+5:45',  '+5:45',  'Katmandu',                  524 ),
            ( '+6:00',  '+6:00',  'Almaty',                    398 ),
            ( '+6:00',  '+6:00',  'Dacca, Dhaka',               50 ),
            ( '+6:00',  '+6:00',  'Astana',                    398 ),
            ( '+6:30',  '+6:30',  'Rangoon',                   104 ),
            ( '+7:00',  '+7:00',  'Novosibirsk',               643 ),
            ( '+7:00',  '+7:00',  'Bangkok',                   764 ),
            ( '+7:00',  '+7:00',  'Vietnam',                   704 ),
            ( '+7:00',  '+7:00',  'Jakarta',                   360 ),
            ( '+8:00',  '+8:00',  'Irkutsk',                   643 ),
            ( '+8:00',  '+8:00',  'Ulaanbaatar',               496 ),
            ( '+8:00',  '+8:00',  'Beijing, Shanghai',         156 ),
            ( '+8:00',  '+8:00',  'Hong Kong SAR',             344 ),
            ( '+8:00',  '+8:00',  'Taipei',                    158 ),
            ( '+8:00',  '+8:00',  'Kuala Lumpur',              458 ),
            ( '+8:00',  '+8:00',  'Singapore',                 702 ),
            ( '+8:00',  '+8:00',  'Perth',                      36 ),
            ( '+9:00',  '+9:00',  'Yakutsk',                   643 ),
            ( '+9:00',  '+9:00',  'Seoul',                     410 ),
            ( '+9:00',  '+9:00',  'Osaka, Sapporo, Tokyo',     392 ),
            ( '+9:30',  '+9:30',  'Darwin',                     36 ),
            ( '+9:30',  '+10:30', 'Adelaide',                   36 ),
            ( '+10:00', '+10:00', 'Vladivostok',               643 ),
            ( '+10:00', '+10:00', 'Guam',                      316 ),
            ( '+10:00', '+10:00', 'Port Moresby',              598 ),
            ( '+10:00', '+10:00', 'Brisbane',                   36 ),
            ( '+10:00', '+11:00', 'Carrera, Melbourne, Sidney', 36 ),
            ( '+10:00', '+11:00', 'Hobart',                     36 ),
            ( '+11:00', '+11:00', 'Magadan',                   643 ),
            ( '+11:00', '+11:00', 'Solomon Islands',            90 ),
            ( '+11:00', '+11:00', 'New Caledonia',             540 ),
            ( '+12:00', '+12:00', 'Kamchatka',                 643 ),
            ( '+12:00', '+13:00', 'Fiji Islands',              242 ),
            ( '+12:00', '+12:00', 'Marshall Islands',          584 ),
            ( '+12:00', '+13:00', 'Auckland, Wellington',      554 ),
            ( '+13:00', '+14:00', 'Independent State of Samoa',882 );

--<eof>--
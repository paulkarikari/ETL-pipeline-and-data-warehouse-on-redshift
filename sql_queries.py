import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS times"


# CREATE TABLES

staging_events_table_create= ("""
 create table staging_events (
        artist varchar,
        auth varchar not null,
        firstName varchar,
        gender char (1),
        itemInSession int not null,
        lastName varchar,
        length numeric,
        level varchar not null,
        location varchar,
        method varchar not null,
        page varchar not null,
        registration numeric,
        sessionId int not null SORTKEY DISTKEY,
        song varchar,
        status int not null,
        ts numeric not null,
        userAgent varchar,
        userId int
    )
""")

staging_songs_table_create = ("""
create table staging_songs (
        num_songs int not null,
        artist_id char (18) not null SORTKEY DISTKEY,
        artist_latitude varchar,
        artist_longitude varchar,
        artist_location varchar,
        artist_name varchar not null,
        song_id char (18) not null,
        title varchar not null,
        duration numeric not null,
        year int not null
    )
""")

songplay_table_create = ("""
CREATE TABLE  IF NOT EXISTS songplays(
    songplay_id int identity(0,1) PRIMARY KEY SORTKEY,
    start_time VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL DISTKEY,
    level VARCHAR (50) NOT NULL,
    song_id VARCHAR(100),
    artist_id VARCHAR(100),
    session_id INTEGER NOT NULL,
    location VARCHAR(50),
    user_agent VARCHAR(255) NOT NULL
);
""")

user_table_create = ("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER  PRIMARY KEY SORTKEY, 
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gender VARCHAR(1) NOT NULL,
    level VARCHAR(5) NOT NULL
);""")

song_table_create = ("""
CREATE TABLE IF NOT EXISTS songs (
    song_id VARCHAR(100) PRIMARY KEY SORTKEY,
    title VARCHAR NOT NULL,
    artist_id VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    duration NUMERIC NOT NULL
);""")

artist_table_create = ("""
CREATE TABLE IF NOT EXISTS artists(
    artist_id VARCHAR PRIMARY KEY SORTKEY, 
    name VARCHAR NULL,
    location VARCHAR NULL,
    latitude VARCHAR NULL,
    longitude VARCHAR NULL
);
""")

time_table_create = ("""
CREATE TABLE IF NOT EXISTS times(
    time_id int identity(0,1) PRIMARY KEY,
    start_time VARCHAR(100) SORTKEY,
    hour INTEGER NOT NULL,
    day INTEGER NOT NULL,
    week INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    weekday INTEGER NOT NULL
);
""")

# STAGING TABLES
ARN = config.get("IAM_ROLE", "ARN")
LOG_DATA= config.get("S3","LOG_DATA")
LOG_JSONPATH = config.get("S3", "LOG_JSONPATH")
SONG_DATA = config.get("S3", "SONG_DATA")

staging_events_copy = ("""
COPY staging_events FROM {}
IAM_ROLE {} FORMAT AS json {} region 'us-west-2'
""").format(LOG_DATA, ARN, LOG_JSONPATH)

staging_songs_copy = ("""
COPY staging_songs FROM {}
IAM_ROLE {} FORMAT JSON 'auto' region 'us-west-2'
""").format(SONG_DATA, ARN)

# FINAL TABLES

songplay_table_insert = ("""
 insert into songplays (
        start_time,
        user_id,
        level,
        song_id,
        artist_id,
        session_id, 
        location, 
        user_agent
    )
    select
        timestamp 'epoch' + e.ts / 1000 * interval '1 second' as start_time,
        e.userId as user_id,
        e.level,
        s.song_id,
        s.artist_id,
        e.sessionId as session_id,
        e.location,
        e.userAgent as user_agent
    from staging_events e
    left join staging_songs s on e.song = s.title and e.artist = s.artist_name
    where e.page = 'NextSong'
""")

user_table_insert = ("""
INSERT INTO users (
    user_id,
    first_name,
    last_name,
    gender,
    level
) SELECT DISTINCT 
    e.userId,
    e.firstName,
    e.lastName,
    e.gender,
    e.level
    FROM staging_events e
    WHERE e.page ='NextSong'


""")

song_table_insert = ("""
INSERT INTO songs (song_id,title,artist_id,year,duration)
SELECT s.song_id,s.title,s.artist_id, s.year, s.duration from staging_songs s
""")

artist_table_insert = ("""
INSERT INTO artists (artist_id, name,location, latitude, longitude)
SELECT DISTINCT artist_id, 
        artist_name as name,
        artist_location as location,
        artist_latitude as latitude,
        artist_longitude as longitude
from staging_songs
""")

time_table_insert = ("""
    INSERT INTO times (
    start_time,
    hour,
    day,
    week,
    month,
    year,
    weekday
    )
    SELECT
        t.start_time,
        extract(hour from t.start_time) as hour,
        extract(day from t.start_time) as day,
        extract(week from t.start_time) as week,
        extract(month from t.start_time) as month,
        extract(year from t.start_time) as year,
        extract(weekday from t.start_time) as weekday
    FROM (
        SELECT DISTINCT
            timestamp 'epoch' + ts / 1000 * interval '1 second' as start_time
        FROM staging_events
        WHERE page = 'NextSong'
    ) t
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]

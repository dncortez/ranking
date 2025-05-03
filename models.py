# coding: utf-8
from sqlalchemy import Column, Date, Float, ForeignKey, Index, String, Table, text
from sqlalchemy.dialects.mysql import DATETIME, INTEGER, LONGTEXT, SMALLINT, TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class AppCountry(Base):
    __tablename__ = 'app_country'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False)
    url_image = Column(String(255), nullable=False)


class AppGame(Base):
    __tablename__ = 'app_game'

    id = Column(INTEGER(11), primary_key=True)
    title = Column(String(255), nullable=False, unique=True)
    url_image = Column(String(255), nullable=False)


class AppMatchtype(Base):
    __tablename__ = 'app_matchtype'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)


class AppMedaltype(Base):
    __tablename__ = 'app_medaltype'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)


t_ausentes = Table(
    'ausentes', metadata,
    Column('nickname', String(255)),
    Column('ranking', Float(asdecimal=True)),
    Column('name', String(255))
)


class AuthGroup(Base):
    __tablename__ = 'auth_group'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(150), nullable=False, unique=True)


class AuthUser(Base):
    __tablename__ = 'auth_user'

    id = Column(INTEGER(11), primary_key=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DATETIME(fsp=6))
    is_superuser = Column(TINYINT(1), nullable=False)
    username = Column(String(150), nullable=False, unique=True)
    first_name = Column(String(30), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(254), nullable=False)
    is_staff = Column(TINYINT(1), nullable=False)
    is_active = Column(TINYINT(1), nullable=False)
    date_joined = Column(DATETIME(fsp=6), nullable=False)


class DjangoContentType(Base):
    __tablename__ = 'django_content_type'
    __table_args__ = (
        Index('django_content_type_app_label_model_76bd3d3b_uniq', 'app_label', 'model', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    app_label = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)


class DjangoMigration(Base):
    __tablename__ = 'django_migrations'

    id = Column(INTEGER(11), primary_key=True)
    app = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    applied = Column(DATETIME(fsp=6), nullable=False)


class DjangoSession(Base):
    __tablename__ = 'django_session'

    session_key = Column(String(40), primary_key=True)
    session_data = Column(LONGTEXT, nullable=False)
    expire_date = Column(DATETIME(fsp=6), nullable=False, index=True)


t_posiciones = Table(
    'posiciones', metadata,
    Column('nickname', String(255)),
    Column('ranking', Float(asdecimal=True)),
    Column('name', String(255))
)


t_presentes_100 = Table(
    'presentes_100', metadata,
    Column('nickname', String(255)),
    Column('ranking', Float(asdecimal=True)),
    Column('last_played', DATETIME(fsp=6))
)


t_presentes_150 = Table(
    'presentes_150', metadata,
    Column('nickname', String(255)),
    Column('ranking', Float(asdecimal=True)),
    Column('last_played', DATETIME(fsp=6))
)


t_resultados = Table(
    'resultados', metadata,
    Column('created', DATETIME(fsp=6)),
    Column('ranking_del_challenging', Float(asdecimal=True)),
    Column('jugador_1', String(255)),
    Column('challenging_score', INTEGER(11)),
    Column('rival_score', INTEGER(11)),
    Column('jugador_2', String(255)),
    Column('ranking_del_rival', Float(asdecimal=True)),
    Column('tipo_match', String(255)),
    Column('torneo', String(255)),
    Column('replay_url', String(2000))
)


class AppChar(Base):
    __tablename__ = 'app_char'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False)
    url_image = Column(String(255))
    game_id = Column(ForeignKey('app_game.id'), nullable=False, index=True)

    game = relationship('AppGame')


class AppLeague(Base):
    __tablename__ = 'app_league'

    id = Column(INTEGER(11), primary_key=True)
    title = Column(String(255), nullable=False, unique=True)
    game_id = Column(ForeignKey('app_game.id'), nullable=False, index=True)
    slug = Column(String(50), nullable=False, unique=True)
    user_id = Column(ForeignKey('auth_user.id'), nullable=False, index=True)
    last_update = Column(DATETIME(fsp=6))

    game = relationship('AppGame')
    user = relationship('AuthUser')


class AuthPermission(Base):
    __tablename__ = 'auth_permission'
    __table_args__ = (
        Index('auth_permission_content_type_id_codename_01ab375a_uniq', 'content_type_id', 'codename', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False)
    content_type_id = Column(ForeignKey('django_content_type.id'), nullable=False)
    codename = Column(String(100), nullable=False)

    content_type = relationship('DjangoContentType')


class AuthUserGroup(Base):
    __tablename__ = 'auth_user_groups'
    __table_args__ = (
        Index('auth_user_groups_user_id_group_id_94350c0c_uniq', 'user_id', 'group_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(ForeignKey('auth_user.id'), nullable=False)
    group_id = Column(ForeignKey('auth_group.id'), nullable=False, index=True)

    group = relationship('AuthGroup')
    user = relationship('AuthUser')


class DjangoAdminLog(Base):
    __tablename__ = 'django_admin_log'

    id = Column(INTEGER(11), primary_key=True)
    action_time = Column(DATETIME(fsp=6), nullable=False)
    object_id = Column(LONGTEXT)
    object_repr = Column(String(200), nullable=False)
    action_flag = Column(SMALLINT(5), nullable=False)
    change_message = Column(LONGTEXT, nullable=False)
    content_type_id = Column(ForeignKey('django_content_type.id'), index=True)
    user_id = Column(ForeignKey('auth_user.id'), nullable=False, index=True)

    content_type = relationship('DjangoContentType')
    user = relationship('AuthUser')


class AppPlayer(Base):
    __tablename__ = 'app_player'
    __table_args__ = (
        Index('app_player_nickname_league_id_2b3193d5_uniq', 'nickname', 'league_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    nickname = Column(String(255), nullable=False)
    ranking = Column(Float(asdecimal=True), nullable=False)
    main_id = Column(ForeignKey('app_char.id'), index=True)
    league_id = Column(ForeignKey('app_league.id'), nullable=False, index=True)
    country_id = Column(INTEGER(11), nullable=False, index=True)
    disabled = Column(TINYINT(1), nullable=False)
    days_remaining = Column(INTEGER(11))
    ranking_alternative = Column(Float(asdecimal=True))
    positioning = Column(INTEGER(11))

    league = relationship('AppLeague')
    main = relationship('AppChar')


class AuthGroupPermission(Base):
    __tablename__ = 'auth_group_permissions'
    __table_args__ = (
        Index('auth_group_permissions_group_id_permission_id_0cd325b0_uniq', 'group_id', 'permission_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    group_id = Column(ForeignKey('auth_group.id'), nullable=False)
    permission_id = Column(ForeignKey('auth_permission.id'), nullable=False, index=True)

    group = relationship('AuthGroup')
    permission = relationship('AuthPermission')


class AuthUserUserPermission(Base):
    __tablename__ = 'auth_user_user_permissions'
    __table_args__ = (
        Index('auth_user_user_permissions_user_id_permission_id_14a6b632_uniq', 'user_id', 'permission_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(ForeignKey('auth_user.id'), nullable=False)
    permission_id = Column(ForeignKey('auth_permission.id'), nullable=False, index=True)

    permission = relationship('AuthPermission')
    user = relationship('AuthUser')


class AppTournament(Base):
    __tablename__ = 'app_tournament'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    league_id = Column(ForeignKey('app_league.id'), nullable=False, index=True)
    champion_id = Column(ForeignKey('app_player.id'), index=True)
    tournament_date = Column(Date)

    champion = relationship('AppPlayer')
    league = relationship('AppLeague')


class AppMedal(Base):
    __tablename__ = 'app_medal'
    __table_args__ = (
        Index('app_medal_tournament_id_player_id_mtype_id_e008e17b_uniq', 'tournament_id', 'player_id', 'mtype_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    mtype_id = Column(ForeignKey('app_medaltype.id'), nullable=False, index=True)
    player_id = Column(ForeignKey('app_player.id'), nullable=False, index=True)
    tournament_id = Column(ForeignKey('app_tournament.id'), nullable=False)

    mtype = relationship('AppMedaltype')
    player = relationship('AppPlayer')
    tournament = relationship('AppTournament')


class AppResult(Base):
    __tablename__ = 'app_result'

    id = Column(INTEGER(11), primary_key=True)
    challenging_score = Column(INTEGER(11), nullable=False)
    rival_score = Column(INTEGER(11), nullable=False)
    created = Column(DATETIME(fsp=6), nullable=False)
    replay_url = Column(String(2000))
    ranking_del_challenging = Column(Float(asdecimal=True), nullable=False)
    ranking_del_rival = Column(Float(asdecimal=True), nullable=False)
    challenging_id = Column(ForeignKey('app_player.id'), nullable=False, index=True)
    loser_player_id = Column(ForeignKey('app_player.id'), index=True)
    mtype_id = Column(ForeignKey('app_matchtype.id'), nullable=False, index=True)
    rival_id = Column(ForeignKey('app_player.id'), nullable=False, index=True)
    tournament_id = Column(ForeignKey('app_tournament.id'), index=True)
    victory_player_id = Column(ForeignKey('app_player.id'), index=True)
    league_id = Column(ForeignKey('app_league.id'), nullable=False, index=True)
    ranking_alt_del_challenging = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))
    ranking_alt_del_rival = Column(Float(asdecimal=True), nullable=False, server_default=text("0"))

    challenging = relationship('AppPlayer', primaryjoin='AppResult.challenging_id == AppPlayer.id')
    league = relationship('AppLeague')
    loser_player = relationship('AppPlayer', primaryjoin='AppResult.loser_player_id == AppPlayer.id')
    mtype = relationship('AppMatchtype')
    rival = relationship('AppPlayer', primaryjoin='AppResult.rival_id == AppPlayer.id')
    tournament = relationship('AppTournament')
    victory_player = relationship('AppPlayer', primaryjoin='AppResult.victory_player_id == AppPlayer.id')

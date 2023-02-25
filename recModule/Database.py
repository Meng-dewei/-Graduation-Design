from sqlalchemy.ext.declarative import declarative_base
from recModule.Config import recConfig
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import ProgrammingError, DatabaseError
from sqlalchemy.pool import NullPool

#生成一个SqlORM 基类
Base = declarative_base()

class Songs(Base):
    """歌曲信息表

    id 用来存储歌曲id\n
    name用来存储歌曲名字\n
    filehash用来储存该歌曲文件的哈希\n
    fingerprinted用来判断该歌曲是否已经进行了fingerprint

    Parameters
    ----------
    Base : _type_
        _description_
    """
    __tablename__ = 'Songs'
    # 表结构
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(64))
    filehash = Column(String(512), index=True)
    fingerprinted = Column(Boolean, default=False)

class Fingerprints(Base):
    """存储指纹表

    id为指纹id\n
    song_id 是外键，记录对应的歌曲信息\n
    fingerprint就是获取到的指纹信息\n
    offset就是该指纹的offset位置

    Parameters
    ----------
    Base : _type_
        _description_
    """
    __tablename__ = 'Fingerprints'
    # 表结构
    id = Column(Integer, autoincrement=True, primary_key=True)
    song_id = Column(Integer, index=False)
    # 指纹长度取决于字符串长度
    fingerprint = Column(String(64), index=True)
    offset = Column(Integer)

def checkDatabase(conn=recConfig.sqlalchemy_address):
    """连接数据库\n

    链接数据库并检查表是否为空

    Parameters
    ----------
    conn : str, optional
        数据库链接, by default recConfig.sqlalchemy_address

    Returns
    -------
    Union[Tuple[bool, int, str], Tuple[bool, str, Any]]
        数据库表非空返回(True, 0, "")否则返回(False, err.code, err.orig)
    """
    try:
        # 链接数据库
        engine = create_engine(conn, poolclass=NullPool)
        #创建与数据库的会话sesson
        DBSession = sessionmaker(bind=engine)
        dbs = DBSession()
        dbs.query(Songs).first()
        dbs.query(Fingerprints).first()
        return (True, 0, "")
    except ProgrammingError as err:
        return (False, err.code, err.orig)
    except DatabaseError as err:
        return (False, err.code, err.orig)

def initSession(conn=recConfig.sqlalchemy_address):
    """session初始化

    初始化连接并创建sessionmaker

    Parameters
    ----------
    conn : str, optional
        数据库链接, by default recConfig.sqlalchemy_address

    Returns
    -------
    Tuple[sessionmaker, MockConnection]
        返回由sessionmaker和数据库引擎engine组成的元组
    """
    engine = create_engine(conn, pool_size=recConfig.max_connection)
    DBSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return DBSession, engine

def createTables(conn=recConfig.sqlalchemy_address):
    """Create tables"""
    try:
        engine = create_engine(conn, poolclass=NullPool)
        Base.metadata.create_all(engine) # 生成数据库表
        return True
    except:
        return False

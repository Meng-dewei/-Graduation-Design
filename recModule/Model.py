from recModule import Database, AudioDecoder, Fingerprint
from recModule.Config import recConfig
from sqlalchemy.orm import scoped_session
import os, gc, threading, multiprocessing

class Audio(object):
    db, db_engine = Database.initSession()

    def __init__(self, filepath, filename, filehash):
        self.filepath = filepath
        self.filename = filename
        self.filehash = filehash
        self.fs = None
        self.channels = None
        self.fingerprints = None
        self.id = None
        self.name = None

    @classmethod
    def initFromFile(cls, filepath):
        """从文件路径初始化\n

        1、将传入路径转为绝对路径: filepath\n
        2、获取路径对应音频文件的hash code: filehash\n
        3、获取音频文件名(不含扩展名): filename

        Parameters
        ----------
        filepath : Any
            音频文件路径

        Returns
        -------
        Audio
            返回(filepath, filename, filehash)属性的音频对象
        """
        filepath = os.path.realpath(filepath)
        filehash = AudioDecoder.generateFilehash(filepath)
        filename = os.path.splitext(os.path.split(filepath)[1])[0]
        return cls(filepath, filename, filehash)

    @classmethod
    def initFromDir(cls, dir):
        """从文件目录初始化\n

        文件目录中具有受支持扩展名的文件进行加密, 生成Audio对象组成的列表

        Parameters
        ----------
        dir : Any
            文件目录

        Returns
        -------
        List[Audio]
            含(filepath, filename, filehash)属性的Audio对象组成的列表audio
        """
        dir = os.path.realpath(dir)
        audio = []
        audiofiles = AudioDecoder.readDir(dir)
        for filepath, filename, filehash in audiofiles:
            audio.append(cls(filepath, filename, filehash))
        return audio

    def isFingerprinted(self):
        """判断音频是否进行fingerprint处理

        Returns
        -------
        bool
            是否进行 fingerprint 处理
        """
        dbs = self.db()
        result = dbs.query(Database.Songs).filter_by(filehash=self.filehash).first()
        if result == None:
            return False
        return result.fingerprinted

    def read(self):
        """通过 Audio对象的 filepath 得到音频的采样频率 fs 和通道数 channels 属性

        """
        self.fs, self.channels = AudioDecoder.read(self.filepath)

    def getFingerprints(self):
        """获得 fingerprints

        通过调用Fingerprint中的相应方法获得fingerprints
        """
        fingerprints = set()
        for channel in self.channels:
            arr = Fingerprint.getSpecgramArr(channel, self.fs)
            peaks = Fingerprint.getConstellationMap(arr)
            del arr
            fp = Fingerprint.getFBHashGenerator(peaks)
            del peaks
            # 获得不同通道的unioin
            fingerprints |= set(fp)

        self.fingerprints = fingerprints
        del fingerprints
        gc.collect()
        return

    def getId(self, new=False):
        """获取id

        根据filehash值获取对应实例的id和name

        Parameters
        ----------
        new : bool, optional
            True为新的实例需要重新添加DB, by default False

        Returns
        -------
        int
            返回对象的id
        """
        dbs = self.db()
        result = dbs.query(Database.Songs).filter_by(filehash=self.filehash).first()
        if result != None:
            self.id = result.id
            self.name = result.name
            return result.id
        if new:
            song0 = Database.Songs(name=self.filename, filehash=self.filehash)
            dbs.add(song0)
            dbs.commit()
            self.id = song0.id
            self.name = self.filename
            dbs.close()
            return song0.id
        else:
            return -1

    def startInsertFingerprints(self, thread_num=recConfig.max_connection, insert_num=recConfig.insert_number):
        dbs = self.db()
        song = dbs.query(Database.Songs).filter_by(id=self.id).first()
        if song.fingerprinted:
            print("This song already be fingerprinted")
            return
        fingerprints = list(self.fingerprints)
        st = 0
        total_threads = []
        running_threads = []
        while True:
            if (st+1)*insert_num > len(fingerprints):
                total_threads.append(_insertFingerprints(st, self.db, self.id, fingerprints[st*insert_num::]))
                break
            else:
                total_threads.append(_insertFingerprints(st, self.db, self.id, fingerprints[st*insert_num:(st+1)*insert_num:]))
            st += 1
        st = 0
        while st < len(total_threads):
            if len(running_threads) < thread_num:
                total_threads[st].start()
                running_threads.append(total_threads[st])
                st += 1
                continue
            for t in running_threads:
                if not t.is_alive():
                    running_threads.remove(t)
        for t in total_threads:
            t.join()
        song.fingerprinted = True
        dbs.commit()
        dbs.close()

    # 单线程
    def insertFingerprints(self):
        """插入数据

        往数据库Fingerprints表中插入对应数据
        """
        ss = scoped_session(self.db)
        dbs = ss()
        song = dbs.query(Database.Songs).fliter_by(id=self.id).first()
        if song.fingerprinted:
            print("This song already be fingerprinted")
            return
        # 插入数据
        dbs.execute(Database.Fingerprints.__table__.insert(), [{"song_id": self.id, "fingerprint": fingerprint, "offset": int(offset)} for fingerprint, offset in self.fingerprints])
        song.fingerprinted = True
        dbs.commit()
        dbs.close()
        ss.remove()

    # 使用单一进程
    def recognize_s(self):
        """识别歌曲

        1、获取输入的音频的fingerprint
        2、对每一个fingerprint，在数据库中的搜索相同的fingerprint，并将指纹对应的歌曲信息，以及offset偏移值保存。
        3、有相同 offset差值 越多的 歌曲 就是识别出的歌曲

        Returns
        -------
        Dict[str, Union[str, int]]
            返回最可能的曲目的 id、name和count
        """
        dbs = self.db()
        matches = []
        songs = {}

        # 获取所有匹配的指纹
        for fingerprint, offest in self.fingerprints:
            # 查找所有与记录匹配的哈希
            result = dbs.query(Database.Fingerprints).filter_by(fingerprint=fingerprint).all()
            for r in result:
                s = dbs.query(Database.Songs).filter_by(id=r.song_id).first()
                matches.append((str(s.id), str(abs(r.offset-offest))))
                if not (str(s.id)) in songs:
                    songs[str(s.id)] = s.name

        posibility = {}
        mostpossible = {"id":"", "name":"", "count":0}
        largest = 0
        for song_id, offest_diff in matches:
            if not song_id in posibility:
                posibility[song_id] = dict()
            if not offest_diff in posibility[song_id]:
                posibility[song_id][offest_diff] = 0
            posibility[song_id][offest_diff] += 1
            if posibility[song_id][offest_diff] > largest:
                largest = posibility[song_id][offest_diff]
                mostpossible["id"] = song_id
                mostpossible["name"] = songs[song_id]
                mostpossible["count"] = largest

        return mostpossible

    # 使用多进程
    def recognize(self):
        ss = scoped_session(self.db)
        dbs = ss()
        matches = []
        p = multiprocessing.Pool()
        result = p.map(_matchFingerprints,(data for data in self.fingerprints))
        p.close()
        p.join()
        for r in result:
            matches.extend(r)
        posibility = {}
        mostpossible = {"id":"","name":"","count":0}
        largest = 0
        for song_id,offest_diff in matches:
            if not song_id in posibility:
                posibility[song_id] = dict()
            if not offest_diff in posibility[song_id]:
                posibility[song_id][offest_diff] = 0
            posibility[song_id][offest_diff] += 1
            if posibility[song_id][offest_diff] > largest:
                largest = posibility[song_id][offest_diff]
                mostpossible["id"] = song_id
                mostpossible["name"] = dbs.query(Database.Songs).filter_by(id=song_id).first().name
                mostpossible["count"] = largest

        dbs.close()
        ss.remove()
        return mostpossible

    def cleanup(self):
        del self.fingerprints
        del self.channels
        gc.collect()

class _insertFingerprints(threading.Thread):
    def __init__(self, threadID, db, song_id, data):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.db = db
        self.song_id = song_id
        self.data = data

    def run(self):
        ss = scoped_session(self.db)
        dbs = ss()
        dbs.execute(Database.Fingerprints.__table__.insert(),[{"song_id":self.song_id,"fingerprint":fingerprint, "offset":int(offset)} for fingerprint, offset in self.data])
        dbs.commit()
        dbs.close()
        ss.remove()


class _getFingerprints(threading.Thread):
    def __init__(self, threadID,audio):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.audio = audio
    def run(self):
        if self.audio.channels is None:
            self.audio.read()
        self.audio.getFingerprints()


def _matchFingerprints(data):
    fp, offset = data
    db, e = Database.initSession()
    ss = scoped_session(db)
    dbs = ss()
    matches = []
    try:
        for r in dbs.query(Database.Fingerprints).filter_by(fingerprint=fp).all():
            s = dbs.query(Database.Songs).filter_by(id=r.song_id).first()
            matches.append((str(s.id), str(abs(r.offset - offset))))
    finally:
        dbs.close()
        ss.remove()

    return matches
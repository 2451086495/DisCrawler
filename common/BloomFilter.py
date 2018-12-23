#encoding=utf-8
import random
import array


class BitMap(object):
    """
    BitMap class
    """

    BITMASK= [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
    BIT_CNT = [bin(i).count("1") for i in range(256)]

    def __init__(self, maxnum=0):
        """
        Create a BitMap
        """
        nbytes = int((maxnum + 7) / 8)
        self.bitmap = array.array('B', [0 for i in range(nbytes)])

    def set(self, pos):
        """
        Set the value of bit@pos to 1
        """
        self.bitmap[int(pos / 8)] |= self.BITMASK[pos % 8]



    def test(self, pos):
        """
        Return bit value
        """
        return (self.bitmap[int(pos / 8)] & self.BITMASK[pos % 8]) != 0

#k = ln2 * m / n 时 误判率 最小， k为hash函数个数，m为bit数，n为预估要插入的数据量
class BloomFilter:
    def __init__(self, mapsize=160000, max_node_size=10000, random_num=8):
        self.m = mapsize
        self.n = max_node_size
        self.k = random_num
        self.bitmap = BitMap(maxnum=self.m)
        self.count = 0;
        pass

    def set(self, string):
        calcmap = self.calcMap(string)
        for x in calcmap:
            self.bitmap.set(x)
        pass

    def test(self, string):
        calcmap = self.calcMap(string)
        for x in calcmap:
            if not self.bitmap.test(x):
                return False
        return True

    def calcMap(self, string):
        r = random.Random(string)
        lv1random = [r.random() for x in range(self.k)]
        return [int(random.Random(x).random()*self.m) for x in lv1random]

    def TestAndSet(self, string):
        bOk = True
        calcmap = self.calcMap(string)
        for x in calcmap:
            if not self.bitmap.test(x):
                bOk = False
                self.bitmap.set(x)
        return bOk

'''
fb = BloomFilter()
print fb.test("agg")
print fb.set("agg")
print fb.test("agg")
'''
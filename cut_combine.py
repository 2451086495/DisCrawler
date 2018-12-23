#encoding=utf-8
import sys
import os
import shutil

DIR = 'dir_'
def Combine(dir):
    list = os.listdir(dir)
    file_list = [os.path.join(dir, file) for file in list]
    file_list.sort()
    if len(file_list) == 0:
        return

    pos = file_list[0].rfind('.')  #找文件名和后缀名的分割点
    if pos == -1:
        print 'files name should has suffix'
        sys.exit()

    global DIR
    file_name = "%s.%s" % (dir[len(DIR):], file_list[0][pos + 1 : ])
    print file_name
    #print "%s.%s" % (dir[len(DIR):], file_list[0][pos + 1 : ]
    with open(file_name, 'w') as f:
        for filename in file_list:
            f.write(open(filename).read())

#file 要分裂的文件
#size 每次分裂的大小，单位为byte
def Cut(file, size):
    pos = file.rfind('.')  #找文件名和后缀名的分割点
    if pos == -1:
        print 'file name should has suffix'
        sys.exit()

    global DIR
    filename = file[ : pos]
    dir = DIR + filename
    suffix = file[pos + 1 : ]
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    idx = 0

    with open(file, 'r') as f:
        cnt = f.read(size)
        while len(cnt) > 0:
            new_file_name = '%s/%s%d.%s' % (dir, filename, idx, suffix)
            with open(new_file_name, 'w') as new_f:
                new_f.write(cnt)
            cnt = f.read(size)
            idx += 1

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'python %s [cut|combine] [file|dir] [size(M) per unit]' % sys.argv[0]
        sys.exit()

    if sys.argv[1] == 'cut':
        if len(sys.argv) != 4:
            print 'python %s cut [file] [size(M) per unit]' % sys.argv[0]
            sys.exit()
        Cut(sys.argv[2], int(sys.argv[3]) << 20)

    elif sys.argv[1] == 'combine':
        if len(sys.argv) != 3:
            print 'python %s combine [dir]' % sys.argv[0]
            sys.exit()
        Combine(sys.argv[2])
    else:
        print 'unkonw cmd %s' % str(sys.argv)






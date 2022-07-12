from subprocess import Popen, PIPE

def createKerberostgt(kuser,kpasswd,realm):
    
    password=str.encode(kpasswd+"\n")
    kinit = '/usr/bin/kinit'
    kinit_args = [ kinit, '%s@%s' % (kuser,realm) ]
    kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    kinit.stdin.write(password)
    kinit.communicate()
    out = subprocess.getoutput('klist')
    print(out)


def destoryKerberostgt():

    kdestroy = '/usr/bin/kdestroy'
    kinit_args = [kdestroy]
    kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    kinit.wait()    


createKerberostgt("tzg","Goeth2021!","NNITCORP.COM")


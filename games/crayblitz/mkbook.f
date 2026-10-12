      program mkbook
c     empty opening books for Cray Blitz: BOOK, BOOKW and BOOKB, each of
c     two records of 100 words, the first word the size (2)
      integer record(100)
      character*5 names(3)
      data names /'BOOK ', 'BOOKW', 'BOOKB'/
      do 300 k=1,3
          open (unit=3,file=names(k),status='NEW',access='DIRECT',
     *          form='UNFORMATTED',recl=800)
          do 100 i=1,100
              record(i)=0
100       continue
          record(1)=2
          write(3,rec=1) record
          record(1)=0
          write(3,rec=2) record
          close (unit=3)
          print 200, names(k)
200       format(' made ',a5)
300   continue
      end

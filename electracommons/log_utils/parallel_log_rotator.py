import logging
import logging.handlers
import os
import time
import re

class ParallelTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    I have created a class ParallelTimedRotatingFileHandler mainly aimed at allowing multiple processes writing in parallel to a log file. 
    The problems with parallel processes solved by this class, are:

    - The rollover moment when all processes are trying to copy or rename the same file at the same time, gives errors.
    - The solution for this problem was exactly the naming convention you suggest. 
        So, for a file name Service that you supply in the handler, logging does not go to e.g. 
        Service.log but today to Service.2014-08-18.log and tomorrow Service.2014-08-19.log.
    - Another solution is to open the files in a (append) mode instead of w to allow parallel writes.
    - Deleting the backup files also needs to be done with caution as multiple parallel processes are deleting the same files at the same time.
    - This implementation does not take into account leap seconds (which is not a problem for Unix). 
        In other OS, it might still be 30/6/2008 23:59:60 at the rollover moment, so the date has not changed, so, we take the same file name as yesterday.
    - I know that the standard Python recommendation is that the logging module is not foreseen for parallel processes, and I should use SocketHandler, but at least in my environment, this works.
    
    The code is just a slight variation of the code in the standard Python handlers.py module. Of course copyright to the copyright holders.
    """
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None, postfix = ".log"):

        self.origFileName = filename
        self.when = when.upper()
        self.interval = interval
        self.backupCount = backupCount
        self.utc = utc
        self.postfix = postfix
        self.atTime = atTime

        if self.when == 'S':
            self.interval = 1 # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$"
        elif self.when == 'M':
            self.interval = 60 # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$"
        elif self.when == 'H':
            self.interval = 60 * 60 # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24 # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7 # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                 raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        currenttime = int(time.time())
        logging.handlers.BaseRotatingHandler.__init__(self, self.calculateFileName(currenttime), 'a', encoding, delay)

        self.extMatch = re.compile(self.extMatch)
        self.interval = self.interval * interval # multiply by units requested

        self.rolloverAt = self.computeRollover(currenttime)

    def calculateFileName(self, currenttime):
        if self.utc:
             timeTuple = time.gmtime(currenttime)
        else:
             timeTuple = time.localtime(currenttime)

        return self.origFileName + "." + time.strftime(self.suffix, timeTuple) + self.postfix

    def getFilesToDelete(self, newFileName):
        dirName, fName = os.path.split(self.origFileName)
        dName, newFileName = os.path.split(newFileName)

        fileNames = os.listdir(dirName)
        result = []
        prefix = fName + "."
        postfix = self.postfix
        prelen = len(prefix)
        postlen = len(postfix)
        for fileName in fileNames:
            if fileName[:prelen] == prefix and fileName[-postlen:] == postfix and len(fileName)-postlen > prelen and fileName != newFileName:
                 suffix = fileName[prelen:len(fileName)-postlen]
                 if self.extMatch.match(suffix):
                     result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        current_time = self.rolloverAt
        new_file_name = self.calculateFileName(current_time)
        new_base_file_name = os.path.abspath(new_file_name)
        self.baseFilename = new_base_file_name
        self.mode = 'a'
        self.stream = self._open()

        if self.backupCount > 0:
            for s in self.getFilesToDelete(new_file_name):
                try:
                    os.remove(s)
                except Exception as _:
                    pass

        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval

        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_now = time.localtime(current_time)[-1]
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    new_rollover_at = new_rollover_at - 3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    new_rollover_at = new_rollover_at + 3600
        self.rolloverAt = new_rollover_at

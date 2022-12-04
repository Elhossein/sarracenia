import logging
import paramiko
import re

import sarracenia
from sarracenia.flowcb import FlowCB

import time


logger = logging.getLogger(__name__)

class Scheduled(FlowCB):

    """
    
    Scheduled flow callback plugin arranges to post url's
    
    at scheduled times. the schedule can be a specified as:
    
    * scheduled_interval 1m   (once a minute) a duration
    * scheduled_hour  4,9    at 4Z and 9Z every day.
    * scheduled_minute 33,45  within scheduled hours which minutes.
    
    Scheduled_interval takes precedence over the others, making it
    easier to specify an interval for testing/debugging purposes.
    
    currently: when using scheduled_hour, only one minute can
      be given within the hour.
    
    use in code:
    
    import scheduled
    
         in the routine...
            self.wait_until_hour()  # comment out for just every hour.
    
            self.wait_for_minute()
    
            # this code works if only invoked once within an hour...
    
    
    Config:
    
    uses self.o.scheduled_hour as a sarracenia option list of hours
    
    uses self.o.scheduled_minute is a sarracenia option list of minutes...
    
    cocorahs: once an hour.
    
        scheduled_minute 25  # once an hour at 25 minutes after the hour.
    
    examples inventoried to build:
    
    dfo_spine: at hours: 5, 11, 17, 23 ... :45
    
        scheduled_hour 5,7,11
        scheduled_hour 17
        scheduled_hour 25
        scheduled_minute 45
    
    grca_timeseries: at 15 and 55 every hour.
    
    manitoba_surface: 20 minutes past each hour.
    
    rwin_bc: 10,20,40,59 past the hour...
    
    trca_precip: 3,18,33,48 past every hour...
    
    yukon_hourly: at 30 minutes past each hour.
    
    
    
    notes to future self:
    
    would there be a more pythonic way of doing this?
    
        https://schedule.readthedocs.io/en/stable/
    
    would probably be dead easy to do multiple minute within hour,
    just haven't thought about it... 

    hmm...
    
    """


    def __init__(self,options):
        super().__init__(options)
        self.o.add_option( 'scheduled_interval', 'duration', 0 )
        self.o.add_option( 'scheduled_hour', 'list', [] )
        self.o.add_option( 'scheduled_minute', 'list', [] )

    def gather(self):

        # for next expected post
        self.wait_until_next()

        if self.stop_requested:
            return []

        logger.info('time to post')

        # always post the same file at different time
        gathered_messages = []

        for relPath in self.o.path:
            st = paramiko.SFTPAttributes()
            m = sarracenia.Message.fromFileInfo(relPath, self.o, st)
            gathered_messages.append(m)

        return gathered_messages

    def wait_seconds(self,sleepfor):
        """
           sleep for the given number of seconds, like time.sleep() but broken into
           shorter naps to be able to honour stop_requested.
        """

        if sleepfor > 10:
            nap=10
        else:
            nap=sleepfor
    
        while sleepfor > 0:
            time.sleep(nap)
            if self.stop_requested:
                break
            sleepfor -= nap

    def wait_until_hour(self):
        now   = time.gmtime()
        # make a flat list from values where comma separated on a single or multiple lines.
        sched_hour = sum([ x.split(',') for x in self.o.scheduled_hour],[])
        hours = list(map( lambda x: int(x), sched_hour )) + [ 24 ]
        for target in hours:
            if now.tm_min >= target: continue
            break
              
        if target >= 24:
            target = 24 + hours[0]    
    
        sleepfor = (target - now.tm_hour) * 60 * 60
        logger.info("sleep for %d sec" % sleepfor )
        self.wait_seconds(sleepfor)    
    
    def wait_within_hour(self):
        global stop_requested
        now   = time.gmtime()
    
        sched_min = sum([ x.split(',') for x in self.o.scheduled_minute ],[])
        minutes = list(map( lambda x: int(x), sched_min)) + [ 60 ]
        minutes.sort()
        logger.debug( f'minutes: {minutes}')
    
        for target in minutes:
            if now.tm_min >= target: continue
            break
              
        if target >= 60:
            target = 60 + minutes[0]
    
        sleepfor =  (target - now.tm_min) * 60
    
        logger.info("sleep for %d sec" % sleepfor )
        self.wait_seconds(sleepfor)    
    
    def wait_until_next( self ):
        if self.o.scheduled_interval > 0:
            self.wait_seconds(self.o.scheduled_interval)
            return
        if len(self.o.scheduled_hour) > 0:
            self.wait_until_hour()
        if len(self.o.scheduled_minute) > 0:
            self.wait_within_hour()


if __name__ == '__main__':
    
        import sarracenia.config
        import types    
        import sarracenia.flow
        options = sarracenia.config.default_config()
        flow = sarracenia.flow.Flow(options)
        flow.o.scheduled_hour= [ '1','3','5',' 7',' 9',' 13','21','23']
        flow.o.scheduled_minute= [ '1,3,5',' 7',' 9',' 13',' 15',' 51','53' ]
        logging.basicConfig(level=logging.DEBUG)
        me = Scheduled(flow.o)
    
        while True:
            logger.info("hoho!")
            me.wait_within_hour()
            logger.info("Do Something!")
            #me.wait_until_hour(flow.o) 

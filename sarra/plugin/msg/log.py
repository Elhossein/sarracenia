from sarra.plugin import Plugin
import logging

logger = logging.getLogger( __name__ ) 

class Log(Plugin):

    def __init__(self,options):

        # FIXME: should a logging module have a loglevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options,'loglevel'):
            logger.setLevel( getattr(logging, options.loglevel.upper()  ) )
        else:
            logger.setLevel( logging.INFO )

    def on_messages(self,worklist):

        for msg in worklist.incoming:
            logger.warning( "received: %s " % msg )

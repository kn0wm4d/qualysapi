#!/usr/bin/env python3
#global
import tempfile
import os
import unittest
import logging
logger = logging.getLogger(__name__)
import pprint

# Setup module level logging. -- workaround nose
# logging.basicConfig(level=logging.DEBUG)

from qualysapi import connect, qcache, config, exceptions
from qualysapi import api_actions, api_objects

#pudb nice debugger
import pudb
# pu.db

class TestAPIMethods(unittest.TestCase):
    '''
    APICache unittest class

    Params
    tf = tempfile
    test_username -- stored if there is a need to use a temporary config during
    the testing process.
    test_password -- also stored if there is a need to use a temporary config
    during testing.
    tfDestroy -- set IFF the config file is a temp file that should be cleaned
    up during tearDown.
    '''

    # set up configuration arguments for later use by config
    tf = None
    test_username = None
    test_password = None
    tfDestroy = False
    def __init__(self, *args, **kwargs):
        '''
        Sets up a unittest api config file if one doesn't exist already
        '''
        #test from relative...

        #check if we have the required test data for unit tests
        self.tcfilename = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'test_data')
        self.tcfilename = os.path.join( self.tcfilename, 'integration-config.cfg')

        # logger.debug('Test Case Config File is ' + self.tcfilename)
        # logger.debug(os.path.isfile(self.tcfilename))

        # if we don't have a unittest configuration file make a temporary
        # file for our unit tests
        if not os.path.isfile(self.tcfilename):
            import getpass

            # right so go ahead up-front for the test and collect a
            # username and password
            self.test_username = input('QualysGuard Username: ')
            self.test_password = getpass.getpass('QualysGuard Password: ')

            # now create a temporary file and save the user/pass for the tests...
            self.tf = tempfile.NamedTemporaryFile(delete=False)
            self.tcfilename = tf.name
            self.tf.close()
            self.tfDestroy = True

        qconf = config.QualysConnectConfig(
                use_ini=True,
                filename=self.tcfilename,
                username=self.test_username,
                password=self.test_password,
                remember_me=True)
        self.instance = connect(config=qconf)
        self.cache_instance = qcache.APICacheInstance(qconf)
        super(TestAPIMethods, self).__init__(*args, **kwargs)

    def test_api_init(self):
        ''' Pulls a list of maps '''
        with self.assertRaises(exceptions.NoConnectionError):
            actions = api_actions.QGActions()

    def subtest_map_list(self, actions):
        ''' Pulls a list of maps'''
        maps = actions.listMaps(state='Finished')
        self.assertIsNotNone(maps)
        self.assertGreaterEqual(len(maps),1)
        for counter,mapr in enumerate(maps):
            logging.debug('%02d:\r%s' % (counter, mapr))
        return [maps[0]]

    def test_kqb_parser_fromfile(self):
        '''Tests the distributed parser against a static sample file.'''
        fname = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'test_data')
        fname = os.path.join( fname, 'tinykb.xml')
        actions = api_actions.QGActions(cache_connection =
                self.cache_instance)
        qkbobs = actions.queryQKB(file=fname)
        self.assertGreaterEqual(len(qkbobs),1)
        logging.debug(pprint.pformat(qkbobs))

    def test_fetch_report(self):
        '''Fetches a map report given test_map_list having completed with
        success.'''
        actions = api_actions.QGActions(cache_connection =
                self.cache_instance)
        map_reports = self.subtest_map_list(actions)
        self.assertIsNotNone(map_reports)
        self.assertGreaterEqual(len(map_reports),1)
        mapr = actions.fetchReport(id=1882082)
        self.assertIsNotNone(mapr)
        self.assertGreaterEqual(len(mapr),1)
        self.assertIsInstance(mapr[0], api_objects.MapReport)
        logging.debug(mapr)
        #now do tests on the map report

    def test_report_list(self):
        ''' Pulls a list of scans'''
        actions = api_actions.QGActions(cache_connection =
                self.cache_instance)
        scans = actions.listScans(state='Finished')
        self.assertGreaterEqual(len(scans),1)
        #for counter,scan in enumerate(scans):
        #    logging.debug('%02d:\r%s' % (counter, scan))

    def test_report_list(self):
        ''' Pulls a list of scans'''
        actions = api_actions.QGActions(cache_connection =
                self.cache_instance)
        scans = actions.listScans(state='Finished')
        self.assertGreaterEqual(len(scans),1)
        #for counter,scan in enumerate(scans):
        #    logger.debug('%02d:\r%s' % (counter, scan))

    def test_ag_query(self):
        """Test AG List from Asset Group API"""
        actions = api_actions.QGActions(cache_connection =
                self.cache_instance)
        agls = actions.assetGroupQuery(truncation_limit='10')
        #pu.db
        self.assertGreaterEqual(len(agls),1)
        logger.debug(pprint.pformat(agls))
        for itm in agls:
            if isinstance(itm, api_objects.AssetGroupList):
                for ag in itm:
                    logger.info('ID: %s, Title: %s' % (ag.id, ag.title))

    def test_host_query(self):
        """Test AG List from Asset Group API"""
        actions = api_actions.QGActions(cache_connection =
                self.cache_instance)
        hosts = actions.hostListQuery(truncation_limit='10',
            details='All/AGs',
            id_min='2507435',
            show_tags=1)
        self.assertGreaterEqual(len(hosts),1)
        logger.debug(pprint.pformat(hosts))

    def test_host_detection_query(self):
        """Test AG List from Asset Group API"""
        actions = api_actions.QGActions(cache_connection =
                self.cache_instance)
        hosts = actions.hostDetectionQuery(truncation_limit='10',show_tags=1)
        self.assertGreaterEqual(len(hosts),1)
        logger.debug(pprint.pformat(hosts))

    def test_itrhost_query(self):
        """Test AG List from Asset Group API"""
        #alter with non-cache connection
        actions = api_actions.QGActions(connection=self.instance)
        max_hosts = 3000
        hosts = actions.iterativeHostListQuery(truncation_limit='1000',
            details='All/AGs',
            id_min=58404470,
            show_tags=1,
            max_hosts=max_hosts)
        self.assertGreaterEqual(len(hosts),max_hosts)
        # type count
        typecount = {}
        for itm in hosts:
            if type(itm) in typecount:
                typecount[type(itm)] += 1
            else:
                typecount[type(itm)] = 1
        logger.debug(pprint.pformat(typecount))
        #logger.debug('Found %d hosts' % (len(hosts)))
        for host in hosts:
            logger.debug(host)

    def test_itrhost_detection_query(self):
        """Test AG List from Asset Group API"""
        #alter with non-cache connection
        #simple_connect = connect(qconf)
        max_ags = 100
        actions = api_actions.QGActions(connection=self.instance)
        hosts = actions.iterativeHostDetectionQuery(truncation_limit=1000,
            details='Basic/AGs',
            show_tags=1,
            max_hosts=max_hosts)
        self.assertGreaterEqual(len(hosts),max_hosts)
        logger.debug('Found %d hosts' % (len(hosts)))
        for host in hosts:
            logger.debug(host)

    def test_itr_asset_group_query(self):
        """Test AG List from Asset Group API"""
        #alter with non-cache connection
        #simple_connect = connect(qconf)
        max_ags = 100
        actions = api_actions.QGActions(connection=self.instance)
#         agls = actions.iterativeAssetGroupQuery(truncation_limit=1000,
#             max_ags=max_ags)
#         total_ags = 0
#         for agl in agls:
#             if isinstance(agl, api_objects.AssetGroupList):
#                 total_ags += len(agl.items())
#         self.assertEquals(total_ags,max_ags)
        agls = actions.iterativeAssetGroupQuery(
            # consumer_prototype = self.consumer,
            truncation_limit   = 10000,
            block=False)
#        logger.debug('Found %d agls' % (len(agls)))

    def test_kqb(self):
        '''Tests the distributed parser against a static sample file.'''
        actions = api_actions.QGActions(connection =
                self.instance)
        args = {
            'details' : 'All',
            'id_min'  : 10000,
            'id_max'  : 10100,
        }
        #pu.db
        qkbobs = actions.queryQKB(**args)
        for qkbvuln in qkbobs:
            logger.debug('Submetrics for "%s"' % qkbvuln.title)
            try:
                qkbcvss = qkbvuln.cvss
                logger.debug('access.vector = %d' % (int(qkbcvss.access.vector)))
                logger.debug('access.complexity = %d' % (int(qkbcvss.access.complexity)))
                logger.debug('authentication = %d' % (int(qkbcvss.authentication)))
                logger.debug('impact.confidentiality = %d' % (int(qkbcvss.impact.confidentiality)))
                logger.debug('impact.integrity = %d' % (int(qkbcvss.impact.integrity)))
                logger.debug('impact.availability = %d' % (int(qkbcvss.impact.availability)))
                logger.debug('exploitability = %d' % (int(qkbcvss.exploitability)))
                logger.debug('remediation_level = %d' % (int(qkbcvss.remediation_level)))
                logger.debug('report_confidence = %d' % (int(qkbcvss.report_confidence)))
            except Exception as e:
                logger.warn(str(e))

#stand-alone test execution
if __name__ == '__main__':
    import nose2
    nose2.main(argv=['fake', '--log-capture',
        #'TestAPIMethods.test_itrhost_query',
        'TestAPIMethods.test_kqb',
        ])


#!/usr/bin/env python

import select
import socket
import sys
import unittest

import pycares


class DNSTest(unittest.TestCase):

    def setUp(self):
        self.channel = pycares.Channel(timeout=1.0, tries=1)

    def tearDown(self):
        self.channel = None

    def wait(self):
        while True:
            read_fds, write_fds = self.channel.getsock()
            if not read_fds and not write_fds:
                break
            timeout = self.channel.timeout()
            if timeout == 0.0:
                self.channel.process_fd(pycares.ARES_SOCKET_BAD, pycares.ARES_SOCKET_BAD)
                continue
            rlist, wlist, xlist = select.select(read_fds, write_fds, [], timeout)
            for fd in rlist:
                self.channel.process_fd(fd, pycares.ARES_SOCKET_BAD)
            for fd in wlist:
                self.channel.process_fd(pycares.ARES_SOCKET_BAD, fd)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyaddr(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        self.channel.gethostbyaddr('127.0.0.1', cb)
        self.wait()

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyaddr6(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        self.channel.gethostbyaddr('::1', cb)
        self.wait()

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyname(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        self.channel.gethostbyname('localhost', socket.AF_INET, cb)
        self.wait()

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyname_small_timeout(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        self.channel = pycares.Channel(timeout=0.5, tries=1)
        self.channel.gethostbyname('localhost', socket.AF_INET, cb)
        self.wait()

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_getnameinfo(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            self.assertEqual(result, ('localhost', 'http'))
        self.channel.getnameinfo(('127.0.0.1', 80), pycares.ARES_NI_LOOKUPHOST|pycares.ARES_NI_LOOKUPSERVICE, cb)
        self.wait()

    def test_query_a(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            for r in result:
                self.assertNotEqual(r.host, None)
                self.assertTrue(r.ttl >= 0)
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()

    def test_query_a_bad(self):
        def cb(result, errorno):
            self.assertEqual(result, None)
            self.assertEqual(errorno, pycares.errno.ARES_ENOTFOUND)
        self.channel.query('hgf8g2od29hdohid.com', pycares.QUERY_TYPE_A, cb)
        self.wait()

    def test_query_a_rotate(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            self.count += 1
        self.count = 0
        self.channel = pycares.Channel(timeout=1.0, tries=1, rotate=True)
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.count, 3)

    def test_query_aaaa(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            for r in result:
                self.assertNotEqual(r.host, None)
                self.assertTrue(r.ttl >= 0)
        self.channel.query('ipv6.google.com', pycares.QUERY_TYPE_AAAA, cb)
        self.wait()

    def test_query_cname(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        self.channel.query('livechat.ripe.net', pycares.QUERY_TYPE_CNAME, cb)
        self.wait()

    def test_query_mx(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            for r in result:
                self.assertTrue(r.ttl >= 0)
        self.channel.query('google.com', pycares.QUERY_TYPE_MX, cb)
        self.wait()

    def test_query_ns(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        self.channel.query('google.com', pycares.QUERY_TYPE_NS, cb)
        self.wait()

    def test_query_txt(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            for r in result:
                self.assertTrue(r.ttl >= 0)
        self.channel.query('google.com', pycares.QUERY_TYPE_TXT, cb)
        self.wait()

    def test_query_soa(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            self.assertTrue(result.ttl >= 0)
        self.channel.query('google.com', pycares.QUERY_TYPE_SOA, cb)
        self.wait()

    def test_query_srv(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            for r in result:
                self.assertTrue(r.ttl >= 0)
        self.channel.query('_xmpp-server._tcp.google.com', pycares.QUERY_TYPE_SRV, cb)
        self.wait()

    def test_query_naptr(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
            for r in result:
                self.assertTrue(r.ttl >= 0)
        self.channel.query('sip2sip.info', pycares.QUERY_TYPE_NAPTR, cb)
        self.wait()

    def test_query_ptr(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        ip = '8.8.8.8'
        self.channel.query(pycares.reverse_address(ip), pycares.QUERY_TYPE_PTR, cb)
        self.wait()

    def test_query_ptr_ipv6(self):
        def cb(result, errorno):
            self.assertEqual(errorno, None)
        ip = '2001:4860:4860::8888'
        self.channel.query(pycares.reverse_address(ip), pycares.QUERY_TYPE_PTR, cb)
        self.wait()

    def test_query_cancelled(self):
        def cb(result, errorno):
            self.assertEqual(errorno, pycares.errno.ARES_ECANCELLED)
        self.channel.query('google.com', pycares.QUERY_TYPE_NS, cb)
        self.channel.cancel()
        self.wait()

    def test_channel_destroyed(self):
        self.channel.destroy()
        self.assertRaises(pycares.AresError, self.channel.gethostbyname, 'google.com', socket.AF_INET, lambda *x: None)

    def test_query_bad_type(self):
        self.assertRaises(ValueError, self.channel.query, 'google.com', 667, lambda *x: None)
        self.wait()

    def test_query_timeout(self):
        def cb(result, errorno):
            self.assertEqual(errorno, pycares.errno.ARES_ETIMEOUT)
        self.channel.servers = ['1.2.3.4']
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()

    def test_reverse_address(self):
        s = '1.2.3.4'
        expected = '4.3.2.1.in-addr.arpa'
        self.assertEqual(pycares.reverse_address(s), expected)

    def test_channel_timeout(self):
        def cb(result, errorno):
            self.assertEqual(errorno, pycares.errno.ARES_ECANCELLED)
        self.channel = pycares.Channel(timeout=0.5, tries=1)
        self.channel.gethostbyname('google.com', socket.AF_INET, cb)
        timeout = self.channel.timeout()
        self.assertTrue(timeout > 0.0)
        self.channel.cancel()
        self.wait()


if __name__ == '__main__':
    unittest.main(verbosity=2)


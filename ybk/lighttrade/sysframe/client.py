#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import requests
import xmltodict
from .protocol import UserProtocol, TradeProtocol

requests.packages.urllib3.disable_warnings()

log = logging.getLogger('sysframe')

class Client(UserProtocol, TradeProtocol):
    def __init__(self,
                 front_url,
                 tradeweb_url):
        """
        :param front_url: http://HOST:PORT/ \
                common_front/checkneedless/user/logon/logon.action
        :param tradeweb_url: http://HOST:PORT/issue_tradeweb/httpXmlServlet
        """
        self.front_url = front_url
        self.tradeweb_url = tradeweb_url
        self.session = requests.Session()
        self.session.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self._reset()

    def _reset(self):
        self.cid = None # customer_id
        self.uid = None # user_id
        self.sid = None # session_id
        self.mid = None # market_id
        self.username = None
        self.password = None
        self.latency = None
        self.time_offset = None

    @property
    def is_logged_in(self):
        return self.sid is not None

    def request_tradeweb(self, protocol, params):
        return self.request_xml(protocol, params, mode='tradeweb')

    def request_front(self, protocol, params):
        return self.request_xml(protocol, params, mode='front')

    def request_xml(self, protocol, params, mode='tradeweb', headers={}):
        """ 发送交易指令

        - 拼接请求成xml
        - 发送
        - 解析返回的请求
        """
        if mode == 'tradeweb':
            url = self.tradeweb_url
        elif mode == 'front':
            url = self.front_url

        xml = self._create_xml(protocol, params)
        log.debug('发送请求 {}: {}'.format(url, xml))
        r = self.session.post(url, headers=headers, data=xml, verify=False)
        result = r.content.decode('gb18030', 'ignore')
        log.debug('收到返回 {}'.format(result))
        if len(result) > 0:
            return xmltodict.parse(result)
        else:
            raise ValueError('请求出错, 请检查请求格式/网络连接')

    def _create_xml(self, protocol, params):
        header = '<?xml version="1.0" encoding="gb2312"?>'
        reqs = []
        for key, value in params.items():
            reqs.append('<{}>{}</{}>'.format(key, value, key))
        req = ''.join(reqs)
        body = '<GNNT><REQ name="{}">{}</REQ></GNNT>'.format(protocol, req)
        return header + body
##############################################################################
#
# CMFDynamicViewFTI
# Copyright (c) 2005 Plone Foundation. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
# Authors:  Martin Aspeli
#           Christian Heimes
#
##############################################################################
"""
"""

__author__ = 'Christian Heimes <tiran@cheimes.de>'
__docformat__ = 'restructuredtext'

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.CMFDynamicViewFTI.tests import CMFDVFTITestCase

import zope.component 
import zope.component.testing
from zope.app.testing import setup
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.publisher.interfaces.browser import IBrowserView        
import zope.app.publisher.browser
import zope.publisher.browser

from Products.CMFCore.utils import getToolByName

from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from Products.CMFDynamicViewFTI.fti import DynamicViewTypeInformation

from Interface.Verify import verifyObject
from Interface.Verify import verifyClass

global _globalCatalogCounter
_globalCatalogCounter = 0

def dummyReindex():
    """Hey, cachefu increments a counter in CacheTool for every
    catalog change, so we get to do it too!
    """

    global _globalCatalogCounter
    _globalCatalogCounter += 1

class DummyFolder(BrowserDefaultMixin):

    def getTypeInfo(self):
        return self.fti

    def hasProperty(self, prop):
        if prop == 'layout':
            return True

    def manage_changeProperties(self, layout):
        self.layout = layout


class TestCachefuBehaviour(CMFDVFTITestCase.CMFDVFTITestCase):
    """Test whether CacheFu is happy with what we're doing.

    Common cases for CacheFu: (authenticated, anonymous) combined with
    (containers, content). 4 cases.

    Anonymous, content -- "Anonymous users are served content object
    views from the proxy cache. These views are purged when content
    objects change." So CacheFu needs to see a real "change" for
    display changes to be recognised by the cache. A reindex_object is
    considered a change, as CMFSquidTool patches the catalog's
    reindexObject().

    Authenticated, content -- "Authenticated users are served pages from
    memory.  Member ID is used in the ETag because content is
    personalized; the time of the last catalog change is included so
    that the navigation tree stays up to date." So a reindexObject
    should be enough in this case for CacheFu.

    Container, both authenticated and anonymous -- "Both anonymous and
    authenticated users are served pages from memory, not the proxy
    cache.  The reason is that we can't easily purge container views
    when they change since container views depend on all of their
    contained objects, and contained objects do not necessarily purge
    their containers' views when they change.  Member ID is used in
    the ETag because content is personalized; the time of the last
    catalog change is included so that the contents and the navigation
    tree stays up to date." A reindexObject is enough here.
    """

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.types = getToolByName(self.portal, 'portal_types')
        self.dfolder = DummyFolder()
        self.dfolder.fti = self.types['DynFolder']
        self.testfolder = self.dfolder
        self.testfolder.reindexObject = dummyReindex
        self.testfolder.reindexObject()

    def test_catalogChangeDisplayChange(self):
        global _globalCatalogCounter
        reindexCountBefore = _globalCatalogCounter
        # Name of the layout is not enforced. This test will break
        # once it is, but I'm probably going to be shot if I add a
        # dependency to ATContentTypes in here (that'd be the easy
        # alternative).
        self.testfolder.setLayout('folder_summary_view')
        global _globalCatalogCounter
        reindexCountAfter = _globalCatalogCounter
        self.failUnless(reindexCountBefore < reindexCountAfter)

    def test_catalogChangeOnDefaultPageChange(self):
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCachefuBehaviour))
    return suite

if __name__ == '__main__':
    framework()

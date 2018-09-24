#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright 2012,2013,2014 transLectures-UPV Team
#  Copyright 2012,2013,2014 transLectures-JSI Team
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
    libdfxp.py: A library/parser for the transLectures-extended DFXP file format.

    Creates an object representation of a TL-dfxp file, allowing the user to
    manipulate the data according to the tL use cases (i.e. choose an specific
    segment among different alternatives stated by one <tl:alt> tag).

    This library also includes a sample main function. You can execute it via
    command-line as follows:

    $> python libdfxp.py <dfxp_file>

"""

#---- module imports ----#

from xml.dom.minidom import parse, parseString, Text, Element
from datetime import datetime
import re
import os
import sys
import io
import textwrap

####---- Global variables ----####

SPECIAL_TOKENS = ['[hesitation]', '<unk>', '~SILENCE~',
                  '~SIL', '~LONGSIL', '[UNKNOWN]', '[SILENCE]']
rSPECIAL_TOKENS = [r'\[hesitation\]', r'<unk>', r'~SILENCE~',
                   r'~SIL', r'~LONGSIL', r'\[UNKNOWN\]', r'\[SILENCE\]']
STATUS_VALUES = ['fully_automatic', 'partially_human', 'fully_human']

# See https://bbc.github.io/subtitle-guidelines/
LINE_LEN = 40

#---- class definitions ----#


class Tl(object):
    """
      Base class with common attributtes and methods that will be
      inherited by the rest of classes.

    """

    def __init__(self):
        self.authorType = None
        self.authorId = None
        self.authorConf = None
        self.wordSegId = None
        self.timeStamp = None
        self.confMeasure = None
        self.begin = None
        self.end = None
        self.dfxp = None
        self.lang = None
        # Attributes proposed by EML
        self.elapsedTime = None
        self.modelId = None
        self.processingSteps = None
        self.audioLength = None
        self.status = None

    def __repr__(self):
        string = ''
        if self.authorType is not None and (self.dfxp.authorType != self.authorType or isinstance(
                self, TlDfxp)):
                string += ' authorType="%s"' % (self.authorType)
        if self.authorId is not None and (self.dfxp.authorId != self.authorId or isinstance(
                self, TlDfxp)):
                string += ' authorId="%s"' % (self.authorId)
        if self.authorConf is not None and (self.dfxp.authorConf != self.authorConf or isinstance(
                self, TlDfxp)):
                string += ' authorConf="%.2f"' % (self.authorConf)
        if self.wordSegId is not None and (self.dfxp.wordSegId != self.wordSegId or isinstance(
                self, TlDfxp)):
                string += ' wordSegId="%s"' % (self.wordSegId)
        if self.timeStamp is not None and (self.dfxp.timeStamp != self.timeStamp or isinstance(self, TlDfxp)):
            tt = self.timeStamp.timetuple()
            timestr = '%04d-%02d-%02dT%02d:%02d:%02d' % (
                tt[0], tt[1], tt[2], tt[3], tt[4], tt[5])
            string += ' timeStamp="%s"' % (timestr)
        # if self.confMeasure is not None and (self.dfxp.confMeasure != self.confMeasure or isinstance(self,TlDfxp)): string += ' confMeasure="%.2f"'%(self.confMeasure)
        if self.confMeasure is not None:
            string += ' confMeasure="%.2f"' % (self.confMeasure)
        if self.begin is not None:
            string += ' begin="%.3f"' % (self.begin)
        if self.end is not None:
            string += ' end="%.3f"' % (self.end)
        if self.elapsedTime is not None:
            string += ' elapsedTime="%s"' % (self.elapsedTime)
        if self.modelId is not None:
            string += ' modelId="%s"' % (self.modelId)
        if self.processingSteps is not None:
            string += ' processingSteps="%s"' % (self.processingSteps)
        if self.audioLength is not None:
            string += ' audioLength="%s"' % (self.audioLength)
        if self.status is not None:
            string += ' status="%s"' % (self.status)
        return string

    def printXml(self, out):
        if self.authorType is not None and (self.dfxp.authorType != self.authorType or isinstance(
                self, TlDfxp)):
                w(out, ' aT="%s"' % (self.authorType))
        if self.authorId is not None and (self.dfxp.authorId != self.authorId or isinstance(
                self, TlDfxp)):
                w(out, ' aI="%s"' % (self.authorId))
        if self.authorConf is not None and (self.dfxp.authorConf != self.authorConf or isinstance(
                self, TlDfxp)):
                w(out, ' aC="%.2f"' % (self.authorConf))
        if self.wordSegId is not None and (self.dfxp.wordSegId != self.wordSegId or isinstance(
                self, TlDfxp)):
                w(out, ' wS="%s"' % (self.wordSegId))
        if self.timeStamp is not None and (self.dfxp.timeStamp != self.timeStamp or isinstance(self, TlDfxp)):
            tt = self.timeStamp.timetuple()
            timestr = '%04d-%02d-%02dT%02d:%02d:%02d' % (
                tt[0], tt[1], tt[2], tt[3], tt[4], tt[5])
            w(out, ' tS="%s"' % (timestr))
        # if self.confMeasure is not None and (self.dfxp.confMeasure != self.confMeasure or isinstance(self,TlDfxp)): w(' confMeasure="%.2f"'%(self.confMeasure))
        if self.confMeasure is not None:
            w(
                out, ' cM="%.2f"' % (self.confMeasure))
        if self.begin is not None:
            w(out, ' b="%.3f"' % (self.begin))
        if self.end is not None:
            w(out, ' e="%.3f"' % (self.end))
        if self.elapsedTime is not None and (self.dfxp.elapsedTime != self.elapsedTime or isinstance(
                self, TlDfxp)):
                w(out, ' eT="%s"' % (self.elapsedTime))
        if self.modelId is not None and (self.dfxp.modelId != self.modelId or isinstance(
                self, TlDfxp)):
                w(out, ' mI="%s"' % (self.modelId))
        if self.processingSteps is not None and (self.dfxp.processingSteps != self.processingSteps or isinstance(
                self, TlDfxp)):
                w(out, ' pS="%s"' % (self.processingSteps))
        if self.audioLength is not None and (self.dfxp.audioLength != self.audioLength or isinstance(
                self, TlDfxp)):
                w(out, ' aL="%s"' % (self.audioLength))
        if self.status is not None and (self.dfxp.status != self.status or isinstance(
                self, TlDfxp)):
                w(out, ' st="%s"' % (self.status))


class TlDfxp(Tl):
    """
        Represents the whole DFXP file.
        "data" attribute contains a sorted list of the elements below the <body> element.
    """

    def __init__(self):
        Tl.__init__(self)
        self.videoId = None
        self.dfxp = self
        self.data = []

    def __repr__(self):
        string = '<tl:document'
        if self.videoId is not None:
            string += ' videoId="%s"' % (self.videoId)
        string += Tl.__repr__(self)
        string += '/>'
        for d in self.data:
            string += '\n\n%s' % (d)
        return string

    def printXml(self, out):
        w(out, '<tl:d')
        if self.videoId is not None:
            w(out, ' vI="%s"' % (self.videoId))
        Tl.printXml(self, out)
        w(out, '/>')

    def toXml(self, data=None):
        """ 
            Returns an string, which contains a TL-dfxp xml representation of the data.
            It allows the user to provide previously manipulated data to be outputed.

            Arguments:
            data -- Sorted list of the Elements that will be outputed (default: self.data class attribute)
        """

        if data is None:
            data = self.data

        lang = 'en'
        if self.lang is not None:
            lang = self.lang

        out = io.StringIO()

        w(out, '<?xml version="1.0" encoding="utf-8"?>\n'
          '<tt xml:lang="'+lang+'" xmlns="http://www.w3.org/2006/04/ttaf1" xmlns:tts="http://www.w3.org/2006/10/ttaf1#style" xmlns:tl="translectures.eu">\n'
          '<head>\n'
          '<tl:d')
        if self.videoId is not None:
            w(out, ' vI="%s"' % (self.videoId))
        Tl.printXml(self, out)
        w(out, '/>\n'
          '</head>\n'
          '<body>')

        for d in data:
            d.printXml(out)

        w(out, '\n'
          '</body>\n'
          '</tt>\n')

        data = out.getvalue()
        out.close()
        return data

    def toText(self, data=None):
        """ 
            Returns an string, which contains just plain text from the transcription/translation.
            It allows the user to provide previously manipulated data to be outputed.

            Arguments:
            data -- Sorted list of the Elements that will be outputed (default: self.data class attribute)
        """

        if data is None:
            data = self.data
        string = ''
        for d in data:
            string += '%s' % (d.toText())
        return string.encode('utf-8')


class TlCurrent(Tl):
    """
        Represents a <tl:current> Element.
        "data" attribute contains a sorted list of the elements below this <tl:current> element.
    """

    def __init__(self, dfxp):
        self.dfxp = dfxp
        self.data = []

    def __repr__(self):
        string = '<tl:current>'
        for d in self.data:
            string += '\n%s' % (d)
        string += '\n</tl:current>'
        return string

    def printXml(self, out):
        w(out, '\n<tl:c>')
        for d in self.data.decode('utf-8'):
            d.printXml(out)
        w(out, '\n</tl:c>')

    def toText(self):
        """ Returns plain text from all child nodes. """
        string = ''
        for d in self.data:
            string += '%s' % (d.toText())
        return string


class TlOrigin(Tl):
    """
        Represents a <tl:origin> Element.
        "data" attribute contains a sorted list of the elements below this <tl:origin> element.
    """

    def __init__(self, dfxp):
        self.dfxp = dfxp
        self.data = []

    def __repr__(self):
        string = '<tl:origin>'
        for d in self.data:
            string += '\n%s' % (d)
        string += '\n</tl:origin>'
        return string

    def printXml(self, out):
        w(out, '\n<tl:o>')
        for d in self.data:
            d.printXml(out)
        w(out, '\n</tl:o>')

    def toText(self):
        """ Returns plain text from all child nodes. """
        string = ''
        for d in self.data:
            string += '%s' % (d.toText())
        return string


class TlAlt(object):
    """
        Represents a <tl:alt> Element.
        "data" attribute contains a sorted list of the elements below this <tl:alt> element.
    """

    def __init__(self, dfxp):
        self.dfxp = dfxp
        self.data = []

    def __repr__(self):
        string = '<tl:alt>'
        for d in self.data:
            string += '\n%s' % (d)
        string += '\n</tl:alt>'
        return string

    def printXml(self, out):
        w(out, '\n<tl:a>')
        for d in self.data:
            d.printXml(out)
        w(out, '\n</tl:a>')

    def toText(self):
        """ Returns plain text from all child nodes. """
        string = ''
        for d in self.data:
            string += '%s' % (d.toText())
        return string


class TlSegment(Tl):
    """
        Represents a <tl:segment> Element.
        "data" attribute contains a sorted list of the elements below this <tl:segment> element.
    """

    def __init__(self, dfxp, sId, begin, end):
        Tl.__init__(self)
        self.dfxp = dfxp
        self.segmentId = sId
        self.begin = begin
        self.end = end
        self.data = []

    def __repr__(self):
        string = '<tl:segment'
        string += ' segmentId="%s"' % (self.segmentId)
        string += Tl.__repr__(self)
        string += '>'
        for d in self.data:
            string += '\n%s' % (d)
        string += '\n</tl:segment>'
        return string

    def printXml(self, out):
        w(out, '\n<tl:s')
        w(out, ' sI="%s"' % (self.segmentId))
        Tl.printXml(self, out)
        w(out, '>')
        for d in self.data:
            d.printXml(out)
        w(out, '\n</tl:s>')

    def toText(self):
        """ Returns plain text from all child nodes. """
        string = ''
        for d in self.data:
            string += '%s ' % (d.toText())
        string += '\n'
        return string


class TlGroup(Tl):
    """
        Represents a <tl:group> Element.
        "data" attribute contains a sorted list of the elements below this <tl:group> element.
    """

    def __init__(self, dfxp, begin, end):
        Tl.__init__(self)
        self.dfxp = dfxp
        self.begin = begin
        self.end = end
        self.data = []

    def __repr__(self):
        string = '<tl:group'
        string += Tl.__repr__(self)
        string += '>'
        for d in self.data:
            string += '\n%s' % (d)
        string += '\n</tl:group>'
        return string

    def printXml(self, out):
        w(out, '\n<tl:g')
        Tl.printXml(self, out)
        w(out, '>')
        for d in self.data:
            d.printXml(out)
        w(out, '\n</tl:g>')

    def toText(self):
        """ Returns plain text from all child nodes. """
        string = ''
        for d in self.data:
            string += d.toText()+' '
        return string


class TlWord(Tl):
    """
      Represents a <tl:word> Element.
      "txt" attribute contains the word that follows this <tl:word> element.

    """

    def __init__(self, dfxp):
        Tl.__init__(self)
        self.dfxp = dfxp
        self.txt = None

    def __repr__(self):
        string = '<tl:w'
        string += Tl.__repr__(self)
        string += '/>'
        string += ' %s' % (self.txt)
        return string

    def printXml(self, out):
        w(out, '\n<tl:w')
        Tl.printXml(self, out)
        w(out, '>%s</tl:w>' % (escape(self.txt)))

    def toText(self):
        """ Returns plain text. """
        return self.txt


class TlRawText(object):
    """
        Represents raw text located inside <tl:segment> or <tl:group> Elements.
        "txt" attribute contains this text.
    """

    def __init__(self, txt):
        self.txt = txt

    def __repr__(self):
        return escape(self.txt)

    def printXml(self, out):
        w(out, '\n%s' % (escape(self.txt)))

    def toText(self):
        """ Returns plain text. """
        return self.txt


class TlDfxpFormatError(Exception):
    """
        Exception that is thrown if the xml format is not compilant with the specifications
        of the TransLectures-DFXP extension.
    """
    pass


class dfxpError(Exception):
    """
        General exception (covering IOError and minidom errors)
    """

    def __init__(self, *args):
        self.args = [a for a in args]


# ---- public functions

def escape(string):
    """ escapes xml-reserved tokens. """
    return re.sub(r'&(?!#\d{4};|amp;|lt;|gt;|quot;|apos;)', '&amp;', string).replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')


def repl(m):
    """ function for ampersand quote """
    cs = m.group(1) + m.group(2)
    if cs[-1:] == ';':
        s = cs
    else:
        s = '&amp;' + cs[1:]
    return s


def parseDfxp(fn):
    """ Open, read, and parse a TL-DFXP file.

    Arguments:
    fn -- tl-dfxp file name.
    """

    dfxp = TlDfxp()
    try:
        fd = open(fn, 'rb')
        data = fd.read().decode('utf-8')
        fd.close()
    except IOError as e:
        raise dfxpError(os.strerror(e.errno), e.errno)

    # quote unquoted ampersands
    data = re.sub(r'(&[^; 	]{0,6})(.?)', repl, data)

    try:
        pxml = parseString(data)
        __handleTt(pxml.getElementsByTagName('tt')[0], dfxp)
    except Exception as e:
        raise dfxpError(e.message)

    return dfxp


def parseStrDfxp(string):
    """ Parse TL-DFXP string.

    Arguments:
    string -- tl-dfxp string.
    """
    dfxp = TlDfxp()
    try:
        pxml = parseString(string)
        __handleTt(pxml.getElementsByTagName('tt')[0], dfxp)
    except Exception as e:
        raise dfxpError(e.message)

    return dfxp


def filterSegment(obj, filt=1):
    """ Filters segment data (special tokens) """
    if filt == 0:  # No filtering
        return obj
    if filt == 1:  # filter special tokens and syntax
        new_data = []
        for d in obj.data:
            if isinstance(d, TlWord):
                if d.txt not in SPECIAL_TOKENS:
                    new_data.append(d)
            elif isinstance(d, TlRawText):
                for token in rSPECIAL_TOKENS:
                    d.txt = re.sub(token, r'', d.txt)
                d.txt = re.sub(
                    r'\s+', r' ', re.sub(r'/([^/]+)/([^/]*)/', r'\2', d.txt))
                new_data.append(d)
            else:
                new_data.append(d)
        obj.data = new_data
        return obj


def filterAlt(obj, doc_ts, policy=2):
    """ 
      Given a <tl:alt>, returns the best alternative (segment)
        according to the specified policy
    """
    if policy == 1:  # return last alternative
        last = None
        last_ts = datetime(1970, 1, 1, 00, 00)
        for d2 in obj.data:
            ts = d2.timeStamp
            if ts is None:
                ts = doc_ts
            if ts is None:
                last = d2
            elif ts > last_ts:
                last = d2
                last_ts = ts
        return last
    elif policy == 2:  # return best alternatives
        max_confMeasure = -1
        max_authorConf = -1
        last_ts = datetime(1970, 1, 1, 00, 00)
        max_seg = None
        human = False
        for d2 in obj.data:
            if d2.authorType == 'human' or (d2.authorType is None and pdfxp.authorType == 'human'):
                human = True
            ts = d2.timeStamp
            if ts is None:
                ts = doc_ts
            if ts is None:
                ts = datetime(1980, 1, 1, 00, 00)
            if not(human):
                if d2.confMeasure > max_confMeasure or (d2.confMeasure == max_confMeasure and ts > last_ts):
                    max_confMeasure = d2.confMeasure
                    last_ts = ts
                    max_seg = d2
            elif human and d2.authorType == 'human':
                if d2.authorConf > max_authorConf or (d2.authorConf == max_authorConf and ts > last_ts):
                    max_authorConf = d2.authorConf
                    last_ts = ts
                    max_seg = d2
        return max_seg
    elif policy == 3:  # return original, former transcription
        first = None
        first_ts = datetime(2180, 1, 1, 00, 00)
        for d2 in obj.data:
            ts = d2.timeStamp
            if ts is None:
                ts = doc_ts
            if ts is None:
                first = d2
            elif ts < first_ts:
                first = d2
                first_ts = ts
        return first
    else:
        return None


def filterDfxp(pdfxp, altFiltPol=2, segFiltPol=1):
    """ Filters the whole DFXP file """
    if altFiltPol == 0:  # return all stuff
        return pdfxp.data
    else:
        filt_data = []
        doc_ts = pdfxp.timeStamp
        for d1 in pdfxp.data:
            if isinstance(d1, TlSegment):
                fs = filterSegment(d1, segFiltPol)
                if fs is None:
                    return None
                filt_data.append(fs)
            elif isinstance(d1, TlAlt):
                seg = filterAlt(d1, doc_ts, altFiltPol)
                if seg is None:
                    return None
                fs = filterSegment(seg, segFiltPol)
                if fs is None:
                    return None
                filt_data.append(fs)
            else:
                return None
        return filt_data


def format_time(t, delim=','):
    """ Timestamp formatting according to the SRT/VTT specs """
    left = int(t)
    h = left/3600
    m = (left % 3600)/60
    s = ((left % 3600) % 60) % 60
    dec = int(str('%.3f' % (t-left))[2:])
    return '%02d:%02d:%02d%c%03d' % (h, m, s, delim, dec)


def convert_dfxp(pdfxp, dfxp_data, form=0):
    """ DFXP object representation to text (extended DFXP, standard DFXP, srt, vtt) """
    if dfxp_data is None:
        dfxp_data = pdfxp.data
    if form == 1:  # standard DFXP
        data = '<tt xml:lang="" xmlns="http://www.w3.org/2006/10/ttaf1">\n <head>\n </head>\n <body>\n  <div>\n'
        for d1 in dfxp_data:
            if isinstance(d1, TlSegment):
                string = ''
                for d2 in d1.data:
                    if isinstance(d2, TlWord) or isinstance(d2, TlRawText):
                        string += '%s ' % (re.sub(r'\s+', r' ',
                                                  re.sub(r'/([^/]+)/([^/]*)/', r'\2', d2.txt)))
                    elif isinstance(d2, TlGroup):
                        for d3 in d2.data:
                            string += '%s ' % (re.sub(r'\s+', r' ',
                                                      re.sub(r'/([^/]+)/([^/]*)/', r'\2', d3.txt)))
                data += '   <p xml:id="%s" begin="%.3fs" end="%.3fs">\n    %s\n   </p>\n' % (
                    str(d1.segmentId), d1.begin, d1.end, string.strip().encode('utf-8'))
        data += '  </div>\n </body>\n</tt>'

    elif form == 2:  # srt
        data = ''
        ii = 1
        for d1 in dfxp_data:
            if isinstance(d1, TlSegment):
                string = ''
                for d2 in d1.data:
                    if isinstance(d2, TlWord) or isinstance(d2, TlRawText):
                        string += '%s ' % (re.sub(r'\s+', r' ',
                                                  re.sub(r'/([^/]+)/([^/]*)/', r'\2', d2.txt)))
                    elif isinstance(d2, TlGroup):
                        for d3 in d2.data:
                            string += '%s ' % (re.sub(r'\s+', r' ',
                                                      re.sub(r'/([^/]+)/([^/]*)/', r'\2', d3.txt)))
                string = textwrap.fill(string, width=LINE_LEN, break_long_words=False)
                beg = format_time(d1.begin, delim=',')
                end = format_time(d1.end, delim=',')
                data += '%s ' % (string.strip())
                ii += 1

    elif form == 3:  # vtt
        data = 'WEBVTT\n\n'
        ii = 1
        for d1 in dfxp_data:
            if isinstance(d1, TlSegment):
                string = ''
                for d2 in d1.data:
                    if isinstance(d2, TlWord) or isinstance(d2, TlRawText):
                        string += '%s ' % (re.sub(r'\s+', r' ',
                                                  re.sub(r'/([^/]+)/([^/]*)/', r'\2', d2.txt)))
                    elif isinstance(d2, TlGroup):
                        for d3 in d2.data:
                            string += '%s ' % (re.sub(r'\s+', r' ',
                                                      re.sub(r'/([^/]+)/([^/]*)/', r'\2', d3.txt)))
                string = textwrap.fill(string.decode(
                    'utf-8'), width=LINE_LEN, break_long_words=False)
                beg = format_time(d1.begin, delim='.')
                end = format_time(d1.end, delim='.')
                data += '%d\n%s --> %s\n%s\n\n' % (ii, beg,
                                                   end, string.strip().encode('utf-8'))
                ii += 1

    else:  # extended DFXP
        data = pdfxp.toXml(dfxp_data)

    return data


def updateSegment(pdfxp, newSeg, refSeg, mods, authorType, authorId, authorConf, timeStamp, intSel):
    """ Updates a DFXP Segment object representation. """
    mi = 0
    mods = sorted(mods, key=lambda x: float(x['range'].split(':')[0]))
    j, k = (float(x) for x in mods[mi]['range'].split(':'))
    N = len(refSeg.toText().strip().split())
    if j == refSeg.begin and k == refSeg.end:  # Batch interaction
        newSeg.data = [TlRawText(escape(mods[mi]['text'].strip()))]
        newSeg.confMeasure = 1
        newSeg.authorType = authorType
        newSeg.authorId = authorId
        newSeg.authorConf = authorConf
        newSeg.timeStamp = timeStamp
    else:  # Intelligent interaction
        segc = 0
        nrw = 0
        newSeg_data = []
        for d2 in refSeg.data:
            try:
                p = (d2.begin, d2.end)
            except:
                return 7  # object has no attribute begin/end
            if p[0] >= j and p[1] <= k and intSel == 0:
                if isinstance(d2, TlGroup):
                    return 4  # prevent modifying groups of words
            elif p[1] < j or p[0] > k:
                try:
                    if isinstance(d2, TlWord):
                        nw = 1
                    elif isinstance(d2, TlGroup):
                        # Assuming TlGrup has only TlRawText as data
                        nw = len(d2.data[0].txt.strip().split())
                    elif isinstance(d2, TlRawText):
                        nw = len(d2.txt.strip().split())
                    else:
                        return 5
                except IndexError:
                    nw = 0  # Unexpected length, but we'll try to continue...
                newSeg_data.append(d2)
                segc += log(d2.confMeasure+0.000000001)
                nrw += nw
            if p[0] == j:
                beg = p[0]
            if p[1] == k:
                end = p[1]
                text = mods[mi]['text'].strip()
                if len(text) > 0:
                    newGroup = TlGroup(pdfxp, beg, end)
                    nwtxt = len(text.split())
                    newGroup.data = [TlRawText(escape(text))]
                    newGroup.confMeasure = 1
                    newGroup.authorType = authorType
                    newGroup.authorId = authorId
                    newGroup.authorConf = authorConf
                    newGroup.timeStamp = timeStamp
                    newSeg_data.append(newGroup)
                    segc += (nwtxt*log(1))
                    nrw += nwtxt
                mi += 1
                try:
                    j, k = (float(x) for x in mods[mi]['range'].split(':'))
                    if j == refSeg.begin and k == refSeg.end:
                        # Batch interaction in intelligent interaction? No sense.
                        return 6
                except IndexError:
                    pass
        if nrw > 0:
            newSeg.data = newSeg_data
            newSeg.timeStamp = timeStamp
            newSeg.confMeasure = exp(segc/float(nrw))
        else:  # like batch interaction
            newSeg.data = []
            newSeg.confMeasure = 1
            newSeg.authorType = authorType
            newSeg.authorId = authorId
            newSeg.authorConf = authorConf
            newSeg.timeStamp = timeStamp
    return 0


def updateDfxp(pdfxp, mod, authorId, authorConf, authorType='human', timeStamp=datetime.now(), altFiltPol=2, segFiltPol=1, intSel=0):
    """ Updates a DFXP object representation, keeping track
        of all changes made in the past with <tl:alt>

    """
    doc_ts = pdfxp.timeStamp
    dmods = {}
    updated = False
    for m in mod:
        if intSel == 1:
            segId = str(m['segId']).split('.')[0]
        else:
            segId = m['segId']
        try:
            dmods[segId] += m['mods']
        except KeyError:
            dmods[segId] = m['mods']
    for i in xrange(len(pdfxp.data)):
        d1 = pdfxp.data[i]
        if isinstance(d1, TlSegment):
            try:
                if intSel == 1:
                    trg_segId = str(d1.segmentId).split('.')[0]
                else:
                    trg_segId = d1.segmentId
                mods = dmods[trg_segId]
            except KeyError:
                continue
            d1 = filterSegment(d1, segFiltPol)
            if d1 is None:
                return 1
            newAlt = TlAlt(pdfxp)
            newAlt.data.append(d1)
            newSeg = TlSegment(pdfxp, d1.segmentId, d1.begin, d1.end)
            res = updateSegment(pdfxp, newSeg, d1, mods, authorType,
                                authorId, authorConf, timeStamp, intSel)
            if res != 0:
                return res
            newAlt.data.append(newSeg)
            pdfxp.data[i] = newAlt
            updated = True
        elif isinstance(d1, TlAlt):
            try:
                if intSel == 1:
                    trg_segId = str(d1.data[0].segmentId).split('.')[0]
                else:
                    trg_segId = d1.data[0].segmentId
                mods = dmods[trg_segId]
            except KeyError:
                continue
            seg = filterAlt(d1, doc_ts, altFiltPol)
            if seg is None:
                return 2
            seg = filterSegment(seg, segFiltPol)
            if seg is None:
                return 3
            if seg.authorId == authorId:
                res = updateSegment(
                    pdfxp, seg, seg, mods, authorType, authorId, authorConf, timeStamp, intSel)
                if res != 0:
                    return res
            else:
                newSeg = TlSegment(
                    pdfxp, d1.data[0].segmentId, seg.begin, seg.end)
                res = updateSegment(
                    pdfxp, newSeg, seg, mods, authorType, authorId, authorConf, timeStamp, intSel)
                if res != 0:
                    return res
                d1.data.append(newSeg)
            updated = True
    if not(updated):
        return 6
    try:
        update_status(pdfxp)
    except:
        pass
    return 0


def update_status(pdfxp):
    filt_data = filterDfxp(pdfxp, altFiltPol=2, segFiltPol=0)
    auto_found = False
    human_found = False
    for d in filt_data:
        if isinstance(d, TlSegment):
            aT = d.authorType if d.authorType is not None else pdfxp.authorType
            if aT == 'automatic':
                auto_found = True
            elif aT == 'human':
                human_found = True
    if auto_found and not(human_found):
        pdfxp.status = 'fully_automatic'
    elif not(auto_found) and human_found:
        pdfxp.status = 'fully_human'
    elif auto_found and human_found:
        pdfxp.status = 'partially_human'
    else:
        pdfxp.status = 'fully_automatic'


""" Fast string generation functions """


def w(sIO, string): sIO.write(string.encode('utf-8'))


def wn(sIO, string): w(sIO, string+'\n')

#---- private functions ----#


def __handleTt(tt, dfxp):
    """ Parses <tt> Element. """
    lang = tt.getAttribute('xml:lang').strip()
    if lang != '':
        dfxp.lang = lang
    __handleHead(tt.getElementsByTagName('head')[0], dfxp)
    __handleBody(tt.getElementsByTagName('body')[0], dfxp)


def __handleHead(head, dfxp):
    """ Parses <head> Element. """
    for n in head.childNodes:
        if isinstance(n, Text):
            continue
        if n.tagName == 'tl:document' or n.tagName == 'tl:d':
            __handleTlDocument(n, dfxp)
        else:
            raise TlDfxpFormatError("Expected <tl:d> at <head>, but found another unexpected element.")


def __handleTlDocument(tl_d, dfxp):
    """ Parses <tl:document> Element. """
    if tl_d.getAttribute('vI') != '':
        dfxp.videoId = tl_d.getAttribute('vI')
    elif tl_d.getAttribute('videoId') != '':
        dfxp.videoId = tl_d.getAttribute('videoId')
    if tl_d.getAttribute('aT') != '':
        dfxp.authorType = tl_d.getAttribute('aT')
    elif tl_d.getAttribute('authorType') != '':
        dfxp.authorType = tl_d.getAttribute('authorType')
    if tl_d.getAttribute('aI') != '':
        dfxp.authorId = tl_d.getAttribute('aI')
    elif tl_d.getAttribute('authorId') != '':
        dfxp.authorId = tl_d.getAttribute('authorId')
    if tl_d.getAttribute('aC') != '':
        dfxp.authorConf = float(tl_d.getAttribute('aC'))
    elif tl_d.getAttribute('authorConf') != '':
        dfxp.authorConf = float(tl_d.getAttribute('authorConf'))
    if tl_d.getAttribute('wS') != '':
        dfxp.wordSegId = tl_d.getAttribute('wS')
    elif tl_d.getAttribute('wordSegId') != '':
        dfxp.wordSegId = tl_d.getAttribute('wordSegId')
    if tl_d.getAttribute('tS') != '':
        timeStomp = tl_d.getAttribute('tS')
        if len(timeStomp) == 10:
            dfxp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            dfxp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    elif tl_d.getAttribute('timeStamp') != '':
        timeStomp = tl_d.getAttribute('timeStamp')
        if len(timeStomp) == 10:
            dfxp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            dfxp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    if tl_d.getAttribute('cM') != '':
        dfxp.confMeasure = float(tl_d.getAttribute('cM'))
    elif tl_d.getAttribute('confMeasure') != '':
        dfxp.confMeasure = float(tl_d.getAttribute('confMeasure'))
    if tl_d.getAttribute('b') != '':
        dfxp.begin = float(tl_d.getAttribute('b'))
    elif tl_d.getAttribute('begin') != '':
        dfxp.begin = float(tl_d.getAttribute('begin'))
    if tl_d.getAttribute('e') != '':
        dfxp.end = float(tl_d.getAttribute('e'))
    elif tl_d.getAttribute('end') != '':
        dfxp.end = float(tl_d.getAttribute('end'))
    if tl_d.getAttribute('eT') != '':
        dfxp.elapsedTime = tl_d.getAttribute('eT')
    elif tl_d.getAttribute('elapsedTime') != '':
        dfxp.elapsedTime = tl_d.getAttribute('elapsedTime')
    if tl_d.getAttribute('mI') != '':
        dfxp.modelId = tl_d.getAttribute('mI')
    elif tl_d.getAttribute('modelId') != '':
        dfxp.modelId = tl_d.getAttribute('modelId')
    if tl_d.getAttribute('pS') != '':
        dfxp.processingSteps = tl_d.getAttribute('pS')
    elif tl_d.getAttribute('processingSteps') != '':
        dfxp.processingSteps = tl_d.getAttribute('processingSteps')
    if tl_d.getAttribute('aL') != '':
        dfxp.audioLength = tl_d.getAttribute('aL')
    elif tl_d.getAttribute('audioLength') != '':
        dfxp.audioLength = tl_d.getAttribute('audioLength')
    if tl_d.getAttribute('st') != '':
        dfxp.status = tl_d.getAttribute('st')
    elif tl_d.getAttribute('status') != '':
        dfxp.status = tl_d.getAttribute('status')

    if dfxp.status is not None and dfxp.status not in STATUS_VALUES:
        raise TlDfxpFormatError('Unexpected status attribute value: %s' % dfxp.status)


def __handleBody(body, dfxp):
    """ Parses <body> Element. """
    for n in body.childNodes:
        if isinstance(n, Element):
            if n.tagName == 'tl:current' or n.tagName == 'tl:c':
                cur = __handleTlCurrent(n, dfxp)
                pass  # ignore current
            elif n.tagName == 'tl:origin' or n.tagName == 'tl:o':
              # org = __handleTlOrigin(n,dfxp)
                pass  # ignore origin completely
            elif n.tagName == 'tl:segment' or n.tagName == 'tl:s':
                seg = __handleTlSegment(n, dfxp)
                dfxp.data.append(seg)
            elif n.tagName == 'tl:alt' or n.tagName == 'tl:a':
                alt = __handleTlAlt(n, dfxp)
                dfxp.data.append(alt)
            else:
                raise TlDfxpFormatError('Expected <tl:c>, <tl:o>, <tl:s> or <tl:a> at <body>, but found another unexpected element.')


def __handleTlCurrent(xcur, dfxp):
    """ Parses <tl:current> Element. """
    cur = TlCurrent(dfxp)
    for n in xcur.childNodes:
        if isinstance(n, Element):
            if n.tagName == 'tl:segment' or n.tagName == 'tl:s':
                seg = __handleTlSegment(n, dfxp)
                dfxp.data.append(seg)
            elif n.tagName == 'tl:alt' or n.tagName == 'tl:a':
                alt = __handleTlAlt(n, dfxp)
                dfxp.data.append(alt)
            else:
                raise TlDfxpFormatError('Expected <tl:s> or <tl:a> at <tl:c>, but found another unexpected element.')
    return cur


def __handleTlOrigin(xorg, dfxp):
    """ Parses <tl:origin> Element. """
    org = TlOrigin(dfxp)
    for n in xorg.childNodes:
        if isinstance(n, Element):
            if n.tagName == 'tl:segment' or n.tagName == 'tl:s':
                seg = __handleTlSegment(n, dfxp)
                dfxp.data.append(seg)
            elif n.tagName == 'tl:alt' or n.tagName == 'tl:a':
                alt = __handleTlAlt(n, dfxp)
                dfxp.data.append(alt)
            else:
                raise TlDfxpFormatError('Expected <tl:s> or <tl:a> at <tl:o>, but found another unexpected element.')
    return org


def __handleTlAlt(xalt, dfxp):
    """ Parses <tl:alt> Element. """
    alt = TlAlt(dfxp)
    for n in xalt.childNodes:
        if isinstance(n, Element):
            if n.tagName == 'tl:segment' or n.tagName == 'tl:s':
                seg = __handleTlSegment(n, dfxp)
                alt.data.append(seg)
            else:
                raise TlDfxpFormatError('Expected <tl:s> element after <tl:a>, but found another unexpected element.')
    return alt


def __handleTlSegment(xseg, dfxp):
    """ Parses <tl:segment> Element. """
    if xseg.getAttribute('sI') != '':
        segId = xseg.getAttribute('sI')
    elif xseg.getAttribute('segmentId') != '':
        segId = xseg.getAttribute('segmentId')
    if xseg.getAttribute('b') != '':
        begin = float(xseg.getAttribute('b'))
    elif xseg.getAttribute('begin') != '':
        begin = float(xseg.getAttribute('begin'))
    if xseg.getAttribute('e') != '':
        end = float(xseg.getAttribute('e'))
    elif xseg.getAttribute('end') != '':
        end = float(xseg.getAttribute('end'))
    seg = TlSegment(dfxp, segId, begin, end)
    if xseg.getAttribute('aT') != '':
        seg.authorType = xseg.getAttribute('aT')
    elif xseg.getAttribute('authorType') != '':
        seg.authorType = xseg.getAttribute('authorType')
    else:
        seg.authorType = dfxp.authorType
    if xseg.getAttribute('aI') != '':
        seg.authorId = xseg.getAttribute('aI')
    elif xseg.getAttribute('authorId') != '':
        seg.authorId = xseg.getAttribute('authorId')
    else:
        seg.authorId = dfxp.authorId
    if xseg.getAttribute('aC') != '':
        seg.authorConf = float(xseg.getAttribute('aC'))
    elif xseg.getAttribute('authorConf') != '':
        seg.authorConf = float(xseg.getAttribute('authorConf'))
    else:
        seg.authorConf = dfxp.authorConf
    if xseg.getAttribute('wS') != '':
        seg.wordSegId = xseg.getAttribute('wS')
    elif xseg.getAttribute('wordSegId') != '':
        seg.wordSegId = xseg.getAttribute('wordSegId')
    else:
        seg.wordSegId = dfxp.wordSegId
    if xseg.getAttribute('tS') != '':
        timeStomp = xseg.getAttribute('tS')
        if len(timeStomp) == 10:
            seg.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            seg.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    elif xseg.getAttribute('timeStamp') != '':
        timeStomp = xseg.getAttribute('timeStamp')
        if len(timeStomp) == 10:
            seg.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            seg.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    else:
        seg.timeStamp = dfxp.timeStamp
    if xseg.getAttribute('cM') != '':
        seg.confMeasure = float(xseg.getAttribute('cM'))
    elif xseg.getAttribute('confMeasure') != '':
        seg.confMeasure = float(xseg.getAttribute('confMeasure'))
    else:
        seg.confMeasure = dfxp.confMeasure
    i = 0
    while i < len(xseg.childNodes):
        n = xseg.childNodes[i]
        if isinstance(n, Text):
            txt = n.data.strip()
            if txt != '':
                seg.data.append(TlRawText(txt))
            i += 1
        elif isinstance(n, Element):
            if n.tagName == 'tl:word' or n.tagName == 'tl:w':
                w = __handleTlWord(n, dfxp)
                seg.data.append(w)
                i += 1
            elif n.tagName == 'tl:group' or n.tagName == 'tl:g':
                grp = __handleTlGroup(n, dfxp)
                seg.data.append(grp)
                i += 1
            elif n.tagName == 'br':
                i += 1
            else:
                raise TlDfxpFormatError('Expected <tl:w> or <tl:g> node, but found another unexpected Element.')
        else:
            raise TlDfxpFormatError('Expected Text or Element Node, but found unexpected XML node.')
    return seg


def __handleTlWord(n, dfxp):
    """ Parses <tl:word> Element. """
    w = TlWord(dfxp)
    if n.getAttribute('b') != '':
        w.begin = float(n.getAttribute('b'))
    elif n.getAttribute('begin') != '':
        w.begin = float(n.getAttribute('begin'))
    if n.getAttribute('e') != '':
        w.end = float(n.getAttribute('e'))
    elif n.getAttribute('end') != '':
        w.end = float(n.getAttribute('end'))
    if n.getAttribute('aT') != '':
        w.authorType = n.getAttribute('aT')
    elif n.getAttribute('authorType') != '':
        w.authorType = n.getAttribute('authorType')
    else:
        w.authorType = dfxp.authorType
    if n.getAttribute('aI') != '':
        w.authorId = n.getAttribute('aI')
    elif n.getAttribute('authorId') != '':
        w.authorId = n.getAttribute('authorId')
    else:
        w.authorId = dfxp.authorId
    if n.getAttribute('aC') != '':
        w.authorConf = float(n.getAttribute('aC'))
    elif n.getAttribute('authorConf') != '':
        w.authorConf = float(n.getAttribute('authorConf'))
    else:
        w.authorConf = dfxp.authorConf
    if n.getAttribute('wS') != '':
        w.wordSegId = n.getAttribute('wS')
    elif n.getAttribute('wordSegId') != '':
        w.wordSegId = n.getAttribute('wordSegId')
    else:
        w.wordSegId = dfxp.wordSegId
    if n.getAttribute('tS') != '':
        timeStomp = n.getAttribute('tS')
        if len(timeStomp) == 10:
            w.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            w.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    elif n.getAttribute('timeStamp') != '':
        timeStomp = n.getAttribute('timeStamp')
        if len(timeStomp) == 10:
            w.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            w.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    else:
        w.timeStamp = dfxp.timeStamp
    if n.getAttribute('cM') != '':
        w.confMeasure = float(n.getAttribute('cM'))
    elif n.getAttribute('confMeasure') != '':
        w.confMeasure = float(n.getAttribute('confMeasure'))
    else:
        w.confMeasure = dfxp.confMeasure
    try:
        n = n.childNodes[0]
    except:
        raise TlDfxpFormatError('<tl:w> tag has no childs.')
    if isinstance(n, Text):
        txt = n.data.strip()
        if txt != '':
            w.txt = txt
        else:
            raise TlDfxpFormatError('Expected word inside <tl:w> tag, but found empty text.')
    else:
        raise TlDfxpFormatError('Expected Text Node inside <tl:w> tag, but found another unexpected XML node.')
    return w


def __handleTlGroup(xgrp, dfxp):
    """ Parses <tl:group> Element. """
    if xgrp.getAttribute('b') != '':
        begin = float(xgrp.getAttribute('b'))
    elif xgrp.getAttribute('begin') != '':
        begin = float(xgrp.getAttribute('begin'))
    if xgrp.getAttribute('e') != '':
        end = float(xgrp.getAttribute('e'))
    elif xgrp.getAttribute('end') != '':
        end = float(xgrp.getAttribute('end'))
    grp = TlGroup(dfxp, begin, end)
    if xgrp.getAttribute('aT') != '':
        grp.authorType = xgrp.getAttribute('aT')
    elif xgrp.getAttribute('authorType') != '':
        grp.authorType = xgrp.getAttribute('authorType')
    else:
        grp.authorType = dfxp.authorType
    if xgrp.getAttribute('aI') != '':
        grp.authorId = xgrp.getAttribute('aI')
    elif xgrp.getAttribute('authorId') != '':
        grp.authorId = xgrp.getAttribute('authorId')
    else:
        grp.authorId = dfxp.authorId
    if xgrp.getAttribute('aC') != '':
        grp.authorConf = float(xgrp.getAttribute('aC'))
    elif xgrp.getAttribute('authorConf') != '':
        grp.authorConf = float(xgrp.getAttribute('authorConf'))
    else:
        grp.authorConf = dfxp.authorConf
    if xgrp.getAttribute('wS') != '':
        grp.wordSegId = xgrp.getAttribute('wS')
    elif xgrp.getAttribute('wordSegId') != '':
        grp.wordSegId = xgrp.getAttribute('wordSegId')
    else:
        grp.wordSegId = dfxp.wordSegId
    if xgrp.getAttribute('tS') != '':
        timeStomp = xgrp.getAttribute('tS')
        if len(timeStomp) == 10:
            grp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            grp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    elif xgrp.getAttribute('timeStamp') != '':
        timeStomp = xgrp.getAttribute('timeStamp')
        if len(timeStomp) == 10:
            grp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%d')
        else:
            grp.timeStamp = datetime.strptime(timeStomp, '%Y-%m-%dT%H:%M:%S')
    else:
        grp.timeStamp = dfxp.timeStamp
    if xgrp.getAttribute('cM') != '':
        grp.confMeasure = float(xgrp.getAttribute('cM'))
    elif xgrp.getAttribute('confMeasure') != '':
        grp.confMeasure = float(xgrp.getAttribute('confMeasure'))
    else:
        grp.confMeasure = dfxp.confMeasure
    i = 0
    while i < len(xgrp.childNodes):
        n = xgrp.childNodes[i]
        if isinstance(n, Text):
            txt = n.data.strip()
            if txt != '':
                grp.data.append(TlRawText(txt))
            i += 1
        elif isinstance(n, Element):
            if n.tagName == 'tl:word' or n.tagName == 'tl:w':
                w = __handleTlWord(n, dfxp)
                seg.data.append(w)
                i += 1
        else:
            raise TlDfxpFormatError('Expected Text or Element Node, but found unexpected XML node.')
    return grp


#---- Main sample function. ----#

if __name__ == '__main__':
    """ Main sample function. """
    policy = 2
    form = 2  # 0,*: extended DFXP, 1: standard DFXP, 2: srt, 3: vtt
    fn = ''
    argc = len(sys.argv)
    try:
        seq = range(1, argc)
        iter = seq.__iter__()
        for ii in iter:
            if sys.argv[ii] == '-p':
                ii += 1
                iter.next()
                if (ii < argc):
                    policy = int(sys.argv[ii])
            elif sys.argv[ii] == '-t':
                ii += 1
                iter.next()
                if (ii < argc):
                    form = int(sys.argv[ii])
            elif sys.argv[ii] == '-h' or sys.argv[ii] == '-?':
                raise
            else:
                if (fn == ''):
                    fn = sys.argv[ii]
                else:
                    raise
        if policy < 0 or policy > 3:
            raise
        if fn == '':
            raise
    except:
        sys.stderr.write(
            'Usage: %s [-p <policy>] [-t <type>] <dfxp_file>\n' % os.path.basename(sys.argv[0]))
        sys.stderr.write('\nPossible policies:\n')
        sys.stderr.write('  -p 0 = no filtering (whole DFXP)\n')
        sys.stderr.write('  -p 1 = last modifications\n')
        sys.stderr.write('  -p 2 = best alternatives (default)\n')
        sys.stderr.write(
            '  -p 3 = original text (non-human oldest or least conf)\n')
        sys.stderr.write('\nPossible types:\n')
        sys.stderr.write('  -t 0 = extended dfxp\n')
        sys.stderr.write('  -t 1 = standard dfxp\n')
        sys.stderr.write('  -t 2 = srt (default)\n')
        sys.stderr.write('  -t 3 = vtt\n')
        sys.exit(1)

    try:
        # Parse xml and return an object representation of the dfxp file
        pdfxp = parseDfxp(fn)
    except dfxpError as e:
        sys.stderr.write('%s: %s\n' % (fn, e.args[0]))
        sys.exit(2)

    dfxp_data = filterDfxp(pdfxp, policy)
    text = convert_dfxp(pdfxp, dfxp_data, form)
    sys.stdout.write(text)

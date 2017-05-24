import unittest
from osmwriter import OSMWriter
from six import StringIO
import xml.etree.ElementTree as ET


class OSMWriterTestCase(unittest.TestCase):
    def testSimple(self):

        string = StringIO()

        xml = OSMWriter(fp=string)
        xml.node(1, 10, 30, {"highway": "yes"}, version=2)
        xml.way(1, {'pub': 'yes'}, [123])
        xml.relation(1, {'type': 'boundary'}, [('node', 1), ('way', 2, 'outer')])
        xml.close(close_file=False)

        # Different python versions can write XML in different ways, (eg order
        # of attributes). This makes simple string comparison fail. So simple
        # parse & dump canonicalises it
        output = ET.tostring(ET.fromstring(string.getvalue()))
        exected_output = ET.tostring(ET.fromstring('<?xml version="1.0" encoding="utf-8"?>\n<osm version="0.6" generator="osmwriter">\n  <node lat="10" version="2" lon="30" id="1">\n    <tag k="highway" v="yes"></tag>\n  </node>\n  <way id="1">\n    <nd ref="123"></nd>\n    <tag k="pub" v="yes"></tag>\n  </way>\n  <relation id="1">\n    <member ref="1" type="node" />\n    <member ref="2" role="outer" type="way" />\n    <tag k="type" v="boundary" />\n  </relation>\n</osm>'))

        self.assertEqual(output, exected_output)


if __name__ == '__main__':
    unittest.main()

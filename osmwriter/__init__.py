from xml.sax.saxutils import XMLGenerator
from six import text_type as t

class OSMWriter(object):
    def __init__(self, filename=None, fp=None):
        if filename:
            self.filename = filename
            self.fp = open(self.filename, 'wb')
        elif fp:
            self.fp = fp

        self.xmlfile = XMLGenerator(self.fp, 'utf-8')

        self.xmlfile.startDocument()
        # TODO include version
        self.xmlfile.startElement("osm", {'version': '0.6', 'generator': 'osmwriter'})

    def close(self, close_file=True):
        self.xmlfile.characters("\n")
        self.xmlfile.endElement("osm")
        self.xmlfile.endDocument()
        if close_file:
            self.fp.close()

    def node(self, id, lat, lon, tags=None, **metadata):
        tags = tags or {}

        self.xmlfile.characters("\n  ")

        attrs = {'id': t(id), 'lat': t(lat),  'lon': t(lon)}
        for key, value in metadata.items():
            attrs[key] = t(value)

        self.xmlfile.startElement("node", attrs)

        for key, value in tags.items():
            self.xmlfile.characters("\n    ")
            self.xmlfile.startElement("tag", {'k': key, 'v': value})
            self.xmlfile.endElement("tag")

        self.xmlfile.characters("\n  ")
        self.xmlfile.endElement("node")

    def way(self, id, tags, nodeids, **metadata):
        tags = tags or {}
        nodeids = nodeids or []

        self.xmlfile.characters("\n  ")
        attrs = {'id': t(id)}
        for key, value in metadata.items():
            attrs[key] = t(value)

        self.xmlfile.startElement("way", attrs)

        for nodeid in nodeids:
            self.xmlfile.characters("\n    ")
            self.xmlfile.startElement("nd", {'ref': t(nodeid)})
            self.xmlfile.endElement("nd")

        for key, value in tags.items():
            self.xmlfile.characters("\n    ")
            self.xmlfile.startElement("tag", {'k': key, 'v': value})
            self.xmlfile.endElement("tag")


        self.xmlfile.characters("\n  ")
        self.xmlfile.endElement("way")


    def relation(self, id, tags, members, **metadata):
        tags = tags or {}

        self.xmlfile.characters("\n  ")
        attrs = {'id': t(id)}
        for key, value in metadata.items():
            attrs[key] = t(value)

        self.xmlfile.startElement("relation", attrs)

        for member in members:
            attrs = {}
            if len(member) == 2:
                type, ref = member
                attrs = {'type': t(type), 'ref': t(ref)}
            else:
                type, ref, role = member
                attrs = {'type': t(type), 'ref': t(ref), 'role': t(role)}
            self.xmlfile.characters("\n    ")
            self.xmlfile.startElement("member", attrs)
            self.xmlfile.endElement("member")


        for key, value in tags.items():
            self.xmlfile.characters("\n    ")
            self.xmlfile.startElement("tag", {'k': key, 'v': value})
            self.xmlfile.endElement("tag")


        self.xmlfile.characters("\n  ")
        self.xmlfile.endElement("relation")



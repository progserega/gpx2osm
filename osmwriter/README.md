[![Build Status](https://travis-ci.org/rory/openstreetmap-writer.svg)](https://travis-ci.org/rory/openstreetmap-writer)

# OpenStreetMap Writer

Write OpenStreetMap data files. Currently only XML format is supported. Pure python. No external dependencies. Supports python 2.6, 2.7, 3.3, 3.4.

# Usage

It'll write to an open file-like object.

    from osmwriter import OSMWriter

    with open("myfile.osm.xml", "w") as fp:
        xml = OSMWriter(fp=string)
        xml.node(1, 10, 30, {"highway": "yes"}, version=2)
        xml.way(1, {'pub': 'yes'}, [123])
        xml.relation(1, {'type': 'boundary'}, [('node', 1), ('way', 2, 'outer')])
        xml.close()

Or you can write directly to a filename:

    from osmwriter import OSMWriter

    xml = OSMWriter("test.osm.xml")
    xml.node(1, 10, 30, {"highway": "yes"}, version=2)
    xml.way(1, {'pub': 'yes'}, [123])
    xml.relation(1, {'type': 'boundary'}, [('node', 1), ('way', 2, 'outer')])
    xml.close()

# Development

I welcome all suggestions and patches. GitHub is the project page: https://github.com/rory/openstreetmap-writer . Tests can be run by `python setup.py test` (or `tox` to run tests on all supported Python versions. 

The version numbers follow Semantic Versioning.

# Copyright / Licence

Copyright (C) 2015  Rory McCann, GNU AGPL. Email me (at rory@technomancy.org) if you need another licence.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public Licence as published by
the Free Software Foundation, either version 3 of the Licence, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public Licence for more details.

You should have received a copy of the GNU Affero General Public Licence
along with this program.  If not, see <http://www.gnu.org/licenses/>.

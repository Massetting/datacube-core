#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


from __future__ import absolute_import, division, print_function

import datetime
import pandas

import pytest
from dateutil import tz

from ..util import isclose

from datacube.api.query import Query, _datetime_to_timestamp, query_group_by
from datacube.model import Range
from datetime import timezone


def test_datetime_to_timestamp():
    assert _datetime_to_timestamp((1990, 1, 7)) == 631670400
    assert _datetime_to_timestamp(datetime.datetime(1990, 1, 7)) == 631670400
    assert _datetime_to_timestamp(631670400) == 631670400
    assert _datetime_to_timestamp('1990-01-07T00:00:00.0Z') == 631670400


def test_query_kwargs():
    from mock import MagicMock

    mock_index = MagicMock()
    mock_index.datasets.get_field_names = lambda: {u'product', u'lat', u'sat_path', 'type_id', u'time', u'lon',
                                                   u'orbit', u'instrument', u'sat_row', u'platform', 'metadata_type',
                                                   u'gsi', 'type', 'id'}

    query = Query(index=mock_index, product='ls5_nbar_albers')
    assert str(query)
    assert query.product == 'ls5_nbar_albers'
    assert query.search_terms['product'] == 'ls5_nbar_albers'

    query = Query(index=mock_index, latitude=(-35, -36), longitude=(148, 149))
    assert query.geopolygon
    assert 'lat' in query.search_terms
    assert 'lon' in query.search_terms

    query = Query(index=mock_index, latitude=-35, longitude=148)
    assert query.geopolygon
    assert 'lat' in query.search_terms
    assert 'lon' in query.search_terms

    query = Query(index=mock_index, y=(-4174726, -4180011), x=(1515184, 1523263), crs='EPSG:3577')
    assert query.geopolygon
    assert 'lat' in query.search_terms
    assert 'lon' in query.search_terms

    query = Query(index=mock_index, y=-4174726, x=1515184, crs='EPSG:3577')
    assert query.geopolygon
    assert 'lat' in query.search_terms
    assert 'lon' in query.search_terms

    query = Query(index=mock_index, y=-4174726, x=1515184, crs='EPSG:3577')
    assert query.geopolygon
    assert 'lat' in query.search_terms
    assert 'lon' in query.search_terms

    query = Query(index=mock_index, time='2001')
    assert 'time' in query.search

    query = Query(index=mock_index, time=('2001', '2002'))
    assert 'time' in query.search

    with pytest.raises(ValueError):
        Query(index=mock_index,
              y=-4174726, coordinate_reference_system='WGS84',
              x=1515184, crs='EPSG:3577')

    with pytest.raises(LookupError):
        Query(index=mock_index, y=-4174726, x=1515184, crs='EPSG:3577', made_up_key='NotReal')

    with pytest.raises(LookupError):
        query_group_by(group_by='magic')

def format_test(start_out, end_out):
    return Range(pandas.to_datetime(start_out, utc=True).to_pydatetime(),
                 pandas.to_datetime(end_out, utc=True).to_pydatetime())

testdata = [
(('2008'),
format_test('2008-01-01T00:00:00', '2008-12-31T23:59:59.999999')),
(('2008', '2008'),
format_test('2008-01-01T00:00:00', '2008-12-31T23:59:59.999999')),
(('2008', '2009'),
format_test('2008-01-01T00:00:00', '2009-12-31T23:59:59.999999')),
(('2008-03', '2009'),
format_test('2008-03-01T00:00', '2009-12-31T23:59:59.999999')),
(('2008-03', '2009-10'),
format_test('2008-03-01T00:00', '2009-10-31T23:59:59.999999')),
(('2008', '2009-10'),
format_test('2008-01-01T00:00', '2009-10-31T23:59:59.999999')),
(('2008-03-03', '2008-11'),
format_test('2008-03-03T00:00:00', '2008-11-30T23:59:59.999999')),
(('2008-11-14', '2008-11-30'),
format_test('2008-11-14T00:00:00', '2008-11-30T23:59:59.999999')),
(('2008-11-14', '2008-11-29'),
format_test('2008-11-14T00:00:00', '2008-11-29T23:59:59.999999')),
(('2008-11-14', '2008-11'),
format_test('2008-11-14T00:00:00', '2008-11-30T23:59:59.999999')),
(('2008-11-14', '2008'),
format_test('2008-11-14T00:00:00', '2008-12-31T23:59:59.999999')),
(('2008-11-14'),
format_test('2008-11-14T00:00:00', '2008-11-14T23:59:59.999999')),
(('2008-11-14', '2009-02-02'),
format_test('2008-11-14T00:00:00', '2009-02-02T23:59:59.999999')),
(('2008-11-14T23:33:57', '2008-11-14 23:33:57'),
format_test('2008-11-14T23:33:57', '2008-11-14T23:33:57.999999')),
(('2008-11-14 23:33', '2008-11-14 23:34'),
format_test('2008-11-14T23:33:00', '2008-11-14T23:34:59.999999')),
(('2008-11-14T23:00:00', '2008-11-14 23:35'),
format_test('2008-11-14T23:00', '2008-11-14T23:35:59.999999')),
(('2008-11-10T11', '2008-11-16 14:01'),
format_test('2008-11-10T11:00', '2008-11-16T14:01:59.999999')),
]


@pytest.mark.parametrize('time_param,expected', testdata)
def test_time_handling(time_param, expected):
    query = Query(time=time_param)
    assert 'time' in query.search_terms
    assert query.search_terms['time'] == expected

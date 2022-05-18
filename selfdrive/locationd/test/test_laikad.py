#!/usr/bin/env python3
import unittest
from datetime import datetime

from diskcache import Cache

from laika import AstroDog
from laika.helpers import ConstellationId

from laika.gps_time import GPSTime
from laika.raw_gnss import GNSSMeasurement
from selfdrive.locationd.laikad import Laikad, create_measurement_msg
from selfdrive.test.openpilotci import get_url
from tools.lib.logreader import LogReader

cache = Cache("cachedir")


@cache.memoize()
def get_log(segs=range(0)):
  logs = []
  for i in segs:
    logs.extend(LogReader(get_url("4cf7a6ad03080c90|2021-09-29--13-46-36", i)))
  return [m for m in logs if m.which() == 'ubloxGnss']


def verify_messages(lr, dog, laikad):
  good_msgs = []
  for m in lr:
    msg = laikad.process_ublox_msg(m.ubloxGnss, dog, m.logMonoTime)
    if msg is not None and len(msg.gnssMeasurements.correctedMeasurements) > 0:
      good_msgs.append(msg)
  return good_msgs


class TestLaikad(unittest.TestCase):

  def test_create_msg_without_errors(self):
    gpstime = GPSTime.from_datetime(datetime.now())
    meas = GNSSMeasurement(ConstellationId.GPS, 1, gpstime.week, gpstime.tow, {'C1C': 0., 'D1C': 0.}, {'C1C': 0., 'D1C': 0.})
    # Fake observables_final to be correct
    meas.observables_final = meas.observables
    msg = create_measurement_msg(meas)

    self.assertEqual(msg.constellationId, 'gps')

  def test_laika_online(self):
    lr = get_log(range(1))

    # Set to offline forces to use ephemeris messages
    dog = AstroDog(use_internet=True)
    laikad = Laikad()
    good_msgs = verify_messages(lr, dog, laikad)

    self.assertEqual(560, len(good_msgs))

if __name__ == "__main__":
  unittest.main()

# Copyright (c) 2018, MD2K Center of Excellence
# - Alina Zaman <azaman@memphis.edu>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from cerebralcortex.core.data_manager.raw.stream_handler import DataSet
from cerebralcortex.cerebralcortex import CerebralCortex
from cerebralcortex.core.datatypes.datastream import DataStream
from cerebralcortex.core.datatypes.datastream import DataPoint
from datetime import datetime, timedelta
from core.computefeature import ComputeFeatureBase


import pprint as pp
import numpy as np
import pdb
import pickle
import uuid
import json
import traceback

feature_class_name = 'WorkingDaysFromBeacon'
BEACON_WORK_BEACON_CONTEXT_STREAM = "org.md2k.data_analysis.feature.v4.beacon.work_beacon_context"

class WorkingDaysFromBeacon(ComputeFeatureBase):
    """ Produce feature from gps location Only the days marked as "Work" in
    "org.md2k.data_analysis.gps_episodes_and_semantic_location" data stream are
    taken.  Among these days, the first time of entering in office location
    according to gps location is taken as arrival time and the last time of
    leaving office office location according to gps location is taken as
    departure time Ofiice arrival time are marked as usual or before_time or
    after_time and staying time is also marked as usual, more_than_usual or
    less_than_usual """

    def listing_all_work_days_from_beacon(self, user_id, all_days):
        """
        Produce and save the list of work_days Works-days are generated by the
        gps location of participant's which is labeled as 'Work' the first time
        of a day is marked as start time and the last time marked as end time
        and sample is saved as 'Office' """

        self.CC.logging.log('%s started processing for user_id %s' %
                            (self.__class__.__name__, str(user_id)))
        work_data = []
        stream_ids = self.CC.get_stream_id(user_id,
                                           BEACON_WORK_BEACON_CONTEXT_STREAM)
        for stream_id in stream_ids:

            for day in all_days:
                beacon_location_data_stream = \
                    self.CC.get_stream(stream_id["identifier"], user_id, day)
                current_day = None  # in beginning current day is null
                for data in beacon_location_data_stream.data:
                    #print(data)
                    if data.sample is None or data.sample[0] != "1":
                        # only the data marked as Work are needed
                        continue

                    d = DataPoint(data.start_time, data.end_time,
                                  data.offset, data.sample)
                    #                     if d.offset:
                    #                         d.start_time += timedelta(milliseconds=d.offset)
                    #                         if d.end_time:
                    #                             d.end_time += timedelta(milliseconds=d.offset)
                    #                         else:
                    #                             continue

                    if d.start_time.date() != current_day:
                        '''
                        when the day in d.start_time.date() is not equal
                        current_day that means its a new day.
                        '''
                        if current_day:
                            temp = DataPoint(data.start_time, data.end_time, data.offset, data.sample)
                            temp.start_time = work_start_time
                            temp.end_time = work_end_time
                            temp.sample = 'work'
                            work_data.append(temp)
                        work_start_time = d.start_time

                        # save the new day as current day
                        current_day = d.start_time.date()

                    work_end_time = d.end_time
                if current_day:
                    temp = DataPoint(data.start_time, data.end_time, data.offset, data.sample)
                    temp.start_time = work_start_time
                    temp.end_time = work_end_time
                    temp.sample = 'work'
                    work_data.append(temp)
        try:
            if len(work_data):
                streams = self.CC.get_user_streams(user_id)
                for stream_name, stream_metadata in streams.items():
                    if stream_name == BEACON_WORK_BEACON_CONTEXT_STREAM:
                        print("Going to pickle the file: ",work_data)

                        self.store_stream(filepath="working_days_from_beacon.json",
                                          input_streams=[stream_metadata],
                                          user_id=user_id,
                                          data=work_data)
                        break
        except Exception as e:
            print("Exception:", str(e))
            print(traceback.format_exc())
        self.CC.logging.log('%s finished processing for user_id %s saved %d '
                            'data points' %
                            (self.__class__.__name__, str(user_id),
                             len(work_data)))

    def process(self, user_id, all_days):
        if self.CC is not None:
            self.CC.logging.log("Processing Working Days")
            self.listing_all_work_days_from_beacon(user_id, all_days)

from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.detection import LogDetectorFactory
import fiji.plugin.trackmate.features.spot.SpotContrastAndSNRAnalyzerFactory as SpotContrastAndSNRAnalyzerFactory
import fiji.plugin.trackmate.features.spot.SpotRadiusEstimatorFactory as SpotRadiusEstimatorFactory
from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking import LAPUtils

import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import sys
import fiji.plugin.trackmate.Spot as Spot
import fiji.plugin.trackmate.features.track.TrackDurationAnalyzer as TrackDurationAnalyzer
import fiji.plugin.trackmate.features.track.TrackBranchingAnalyzer as TrackBranchingAnalyzer
import fiji.plugin.trackmate.features.spot.SpotIntensityAnalyzerFactory as SpotIntensityAnalyzerFactory
import fiji.plugin.trackmate.features.track.TrackSpeedStatisticsAnalyzer as TrackSpeedStatisticsAnalyzer
import fiji.plugin.trackmate.features.spot.SpotContrastAndSNRAnalyzer as SpotContrastAndSNRAnalyzer
import fiji.plugin.trackmate.features.spot.SpotRadiusEstimator as SpotRadiusEstimator

from ij import IJ
from ij import WindowManager
from ij.plugin.frame import RoiManager
from ij.gui import Roi
from ij.gui import PointRoi
from ij.gui import OvalRoi
from ij.gui import Plot
from ij.measure import ResultsTable

from util.opencsv import CSVWriter
from java.io import FileWriter
from java.lang import String
from jarray import array as jarr
from java.util import Collections
import os
from collections import Counter as Counter

inputdir = "/Users/bramalingam/Desktop/test/"
files = os.listdir(inputdir)
filelist = []
for file1 in files:
    print file1
    if file1.endswith("R3D_PRJ.dv"):
        filelist.append(file1)

resultstable = ResultsTable()
trackrowNumber = 0
for file1 in filelist:
    filename = inputdir + file1
    IJ.run("Close All", "");
    imp = IJ.run("Bio-Formats Importer", ("open=" + filename + " autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT"))
    imp = WindowManager.getCurrentImage()
    IJ.run(imp, "Subtract Background...", "rolling=50 sliding disable stack");
    dx = imp.getCalibration().pixelWidth
    dy = imp.getCalibration().pixelHeight

    #----------------------------
    # Create the model object now
    #----------------------------

    # Some of the parameters we configure below need to have
    # a reference to the model at creation. So we create an
    # empty model now.

    model = Model()

    # Send all messages to ImageJ log window.
    model.setLogger(Logger.IJ_LOGGER)

    #------------------------
    # Prepare settings object
    #------------------------

    settings = Settings()
    model.getLogger().log('')
    model.getLogger().log('Filename' + file1 + "TEST:" + str(file1.endswith("*R3D_PRJ.dv")))
    settings.setFrom(imp)

    # Configure detector - We use the Strings for the keys
    settings.detectorFactory = LogDetectorFactory()
    settings.detectorSettings = {
        'DO_SUBPIXEL_LOCALIZATION' : True,
        'RADIUS' : 5.0,
        'TARGET_CHANNEL' : 1,
        'THRESHOLD' : 20.0,
        'DO_MEDIAN_FILTERING' : False,
    }

    # Configure spot filters - Classical filter on quality
    filter1 = FeatureFilter('STANDARD_DEVIATION', 530.6, True)
    settings.addSpotFilter(filter1)

    # Configure tracker - We want to allow merges and fusions
    settings.trackerFactory = SparseLAPTrackerFactory()
    settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap() # almost good enough
    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True
    settings.trackerSettings['ALLOW_TRACK_MERGING'] = True
    settings.trackerSettings['LINKING_MAX_DISTANCE'] = 15.0
    settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 15.0
    settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = 10.0
    settings.trackerSettings['MAX_FRAME_GAP']= 2

    settings.addSpotAnalyzerFactory(SpotIntensityAnalyzerFactory())
    settings.addSpotAnalyzerFactory(SpotContrastAndSNRAnalyzerFactory())
    settings.addSpotAnalyzerFactory(SpotRadiusEstimatorFactory())

    # Add an analyzer for some track features, such as the track mean speed.
    settings.addTrackAnalyzer(TrackSpeedStatisticsAnalyzer())
    settings.addTrackAnalyzer(TrackBranchingAnalyzer())
#    settings.initialSpotFilterValue = 1

    #-------------------
    # Instantiate plugin
    #-------------------

    trackmate = TrackMate(model, settings)

    #--------
    # Process
    #--------

    ok = trackmate.checkInput()
    if not ok:
        sys.exit(str(trackmate.getErrorMessage()))

    ok = trackmate.process()
    if not ok:
        sys.exit(str(trackmate.getErrorMessage()))


    #----------------
    # Display results
    #----------------

    # The feature model, that stores edge and track features.
    fm = model.getFeatureModel()
    rm = RoiManager.getInstance()
    if not rm:
          rm = RoiManager()
    rm.reset()
    nextRoi = 0

    for id in model.getTrackModel().trackIDs(True):

        # Fetch the track feature from the feature model.
        v = fm.getTrackFeature(id, 'TRACK_MEAN_SPEED')
        v1 = fm.getTrackFeature(id, TrackBranchingAnalyzer.NUMBER_SPLITS)

        if (v1>0):
            model.getLogger().log('')
            model.getLogger().log('Track ' + str(id) + ': branching = ' + str(v1))
            track = model.getTrackModel().trackSpots(id)
            sortedTrack = list( track )
            Collections.sort( sortedTrack, Spot.frameComparator )

            table = ResultsTable()
            rowNumber = 0
            for spot in sortedTrack:
                sid = spot.ID()
                
                # Fetch spot features directly from spot.
                x=spot.getFeature('POSITION_X')
                y=spot.getFeature('POSITION_Y')
                t=spot.getFeature('FRAME')
                q=spot.getFeature('QUALITY')
                snr=spot.getFeature('SNR')
                mean=spot.getFeature('MEAN_INTENSITY')
                std = spot.getFeature('STANDARD_DEVIATION')
                estdia = spot.getFeature('ESTIMATED_DIAMETER')
                model.getLogger().log('\tspot ID = ' + str(sid) + ': x='+str(x)+', y='+str(y)+', t='+str(t)+', q='+str(q) + ', snr='+str(snr) + ', mean = ' + str(mean))

                table.setValue("TRACK_ID", rowNumber, id)
                table.setValue("POSITION_X", rowNumber, x)
                table.setValue("POSITION_Y", rowNumber, y)
                table.setValue("FRAME", rowNumber, t)
                table.setValue("MEAN_INTENSITY", rowNumber, mean)
                table.setValue("STANDARD_DEVIATION", rowNumber, std)
                table.setValue("SNR", rowNumber, snr)
                rowNumber = rowNumber + 1

#                roi1 = PointRoi(x/dx, y/dy)
#                roi1.setPosition(int(t))
#                rm.add(imp, roi1, nextRoi)
#                nextRoi = nextRoi+1
            
            frame = table.getColumn(3)
            mean = table.getColumn(4)
            std = table.getColumn(5)
            snr = table.getColumn(6)
            var = [s / m for s,m in zip(std, mean)]
            
            from collections import Counter as Counter
            idxvec = [item for item, count in Counter(frame).items() if count > 1]

            if idxvec == []:
                continue
            division = min(idxvec)
            idx = frame.index(division)+1
            mean = mean[:idx]
            frame = frame[:idx]
            std = std[:idx]
            var = var[:idx]
            tempvar = [j-i for i, j in zip(var[:(idx-4)], var[4:])]
            if tempvar == []:
                continue
            idx = tempvar.index(max(tempvar))
            start = frame[0]
            metaphase = frame[idx+3]
            
            if (division - start > 15 and division - start < 100):
                if start>0:
                    for spot in sortedTrack:

                        # Fetch spot features directly from spot.
                        x=spot.getFeature('POSITION_X')
                        y=spot.getFeature('POSITION_Y')
                        t=spot.getFeature('FRAME')
                        roi2 = OvalRoi(x/dx - (6*dx), y/dy - (6*dy), 12, 12)
                        roi2.setPosition(int(t))
                        rm.add(imp, roi2, nextRoi)
                        nextRoi = nextRoi+1
                    resultstable.setValue("IMAGE_NAME", trackrowNumber, filename)
                    resultstable.setValue("TRACK_ID", trackrowNumber, id)
                    resultstable.setValue("START", trackrowNumber, start)
                    resultstable.setValue("METAPHASE", trackrowNumber, metaphase)
                    resultstable.setValue("END", trackrowNumber, division)

                    trackrowNumber = trackrowNumber + 1
#                    plot = Plot(str(id), "slice", "mean", frame, var) 
#                    plot.show()
#                    break

#        imp.close()
resultstable.show("Results")     

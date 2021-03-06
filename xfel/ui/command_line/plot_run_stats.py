from __future__ import division

'''
Author      : Young, I.D.
Created     : 07/14/2016
Last Changed: 07/14/2016
Description : XFEL UI plot real-time run stats
'''

from libtbx.phil import parse
from libtbx.utils import Sorry
from xfel.ui import db_phil_str
from xfel.ui.db.xfel_db import xfel_db_application
from xfel.ui.db.stats import HitrateStats
from xfel.ui.components.run_stats_plotter import plot_multirun_stats
import sys

phil_str = """
  run = None
    .type = int
    .multiple = True
  trial = None
    .type = int
  rungroup = None
    .type = int
  hit_cutoff = 30
    .type = int
    .help = Number of reflections to consider an image a hit. Estimate by looking at plot of strong reflections/image.
  d_min = None
    .type = float
    .help = Highest resolution to consider for I/sigI plot
  compress_runs = True
    .type = bool
    .help = When plotting multiple runs, adjust timestamps so there is no blank space between them.
    .help = Thise mode is not compatible with fetching events from timestamps.
"""
phil_scope = parse(phil_str + db_phil_str)

def run(args):
  user_phil = []
  for arg in args:
    try:
      user_phil.append(parse(arg))
    except Exception, e:
      raise Sorry("Unrecognized argument %s"%arg)
  params = phil_scope.fetch(sources=user_phil).extract()

  app = xfel_db_application(params)
  runs = []
  all_results = []
  if params.rungroup is None:
    assert len(params.run) == 0
    trial = app.get_trial(trial_number = params.trial)
    for rungroup in trial.rungroups:
      for run in rungroup.runs:
        stats = HitrateStats(app, run.run, trial.trial, rungroup.id, params.d_min)()
        if len(stats[0]) > 0:
          runs.append(run.run)
          all_results.append(stats)
  else:
    for run_no in params.run:
      runs.append(run_no)
      all_results.append(HitrateStats(app, run_no, params.trial, params.rungroup, params.d_min)())
  plot_multirun_stats(all_results, runs, params.d_min, n_strong_cutoff=params.hit_cutoff, \
    interactive=True, compress_runs=params.compress_runs)

if __name__ == "__main__":
  run(sys.argv[1:])

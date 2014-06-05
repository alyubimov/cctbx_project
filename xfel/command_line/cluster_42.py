# LIBTBX_SET_DISPATCHER_NAME cluster.42
from __future__ import division
__author__ = 'zeldin'

import logging
from xfel.clustering.cluster import Cluster
from xfel.clustering.cluster_groups import unit_cell_info
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

FORMAT = '%(levelname)s %(module)s.%(funcName)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

def run(_args):
  if _args < 2:
    raise IOError("Must give at least one path to folder of pickles")

  ucs = Cluster.from_directories(_args.folders, "cluster_42")
  logging.info("Data imported.")

  #  Set up mega-plot
  plt.figure(figsize=(22,15))
  gs = gridspec.GridSpec(2,3, height_ratios=[1, 4])
  orr_axes = [plt.subplot(gs[0, 0]),
              plt.subplot(gs[0, 1]),
              plt.subplot(gs[0, 2])]
  clust_ax = plt.subplot(gs[1, :])


  orr_axes = ucs.visualise_orientational_distribution(orr_axes, cbar=False)
  clusters, cluster_ax = ucs.ab_cluster(_args.t, log=_args.log, ax=clust_ax)

  #plt.text("cluster.42 Plot Everything!")
  plt.tight_layout()

  print unit_cell_info(clusters)
  plt.show()

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description=('Create a smorgasboard mega-'
                                                'plot for visualising a set of'
                                                ' integration results.'))
  parser.add_argument('folders', type=str, nargs='+',
                      help='One or more folers containing integration pickles.')
  parser.add_argument('-t', type=float, default=5000,
                      help='threshold value for the unit cell clustering. '
                           'Default = 5000')
  parser.add_argument('-o', type=str, default='clustering',
                      help='output file name for unit cells.')
  parser.add_argument('--log', action='store_true',
                      help="Display the dendrogram with a log scale")
  args = parser.parse_args()
  run(args)

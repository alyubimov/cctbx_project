from __future__ import division

from cctbx.array_family import flex
from smtbx import structure_factors
from cctbx import sgtbx, uctbx, xray, crystal, miller, eltbx
import cctbx.eltbx.wavelengths
import smtbx.development
import smtbx.development
import smtbx.structure_factors.direct as structure_factors
from libtbx.test_utils import approx_equal
import libtbx.utils
import math, random
from libtbx.itertbx import islice, izip
from scitbx import matrix
from scitbx.math import median_statistics


class test_case(object):

  def __init__(self, inelastic_scattering):
    self.inelastic_scattering = inelastic_scattering

  def random_structure(self, space_group_info, set_grads):
    xs = smtbx.development.random_xray_structure(
      space_group_info,
      elements="random",
      n_scatterers=5,
      u_iso_xor_u_aniso=False,
      use_u_aniso=True,
      use_u_iso=True,
      random_u_iso=True,
    )
    if self.inelastic_scattering:
      xs.set_inelastic_form_factors(
        photon=eltbx.wavelengths.characteristic('Mo'),
        table="sasaki")
    for sc in xs.scatterers():
      (
        sc.flags.set_grad_site(set_grads)
                .set_grad_u_iso(set_grads).set_grad_u_aniso(set_grads)
                .set_grad_occupancy(set_grads)
      )
      assert sc.flags.use_u_iso()
      assert sc.flags.use_u_aniso()
    return xs

  def miller_indices(self, space_group_info):
    space_group = space_group_info.group()
    return flex.miller_index(miller.index_generator(
      space_group.type(),
      anomalous_flag=True,
      max_index=(10, 10, 10)))


class consistency_test_cases(test_case):

  def __init__(self, n_directions, inelastic_scattering):
    super(consistency_test_cases, self).__init__(inelastic_scattering)
    self.n_directions = n_directions

  def structures_forward(self, xs, xs_forward, eta_norm):
    while True:
      direction = flex.random_double(xs.n_parameters_XXX())
      direction /= direction.norm()
      eta = eta_norm * direction

      i = 0
      for sc_forward, sc in izip(xs_forward.scatterers(), xs.scatterers()):
        eta_site = matrix.col(eta[i:i+3])
        eta_iso = eta[i+3]
        eta_aniso = matrix.col(eta[i+4:i+10])
        eta_occ = eta[i+10]
        i += 11

        sc_forward.site = matrix.col(sc.site) + eta_site
        sc_forward.u_iso = sc.u_iso + eta_iso
        sc_forward.u_star = matrix.col(sc.u_star) + eta_aniso
        sc_forward.occupancy = sc.occupancy + eta_occ
      yield direction
  structures_forward = classmethod(structures_forward)

  def exercise(self, space_group_info, verbose=False):
    sg = space_group_info.group()
    origin_centric_case = sg.is_origin_centric()

    xs = self.random_structure(space_group_info, set_grads=True)
    indices = self.miller_indices(space_group_info)
    f_calc_linearisation = (
      structure_factors.linearisation_of_f_calc_modulus_squared(xs))

    if (xs.space_group().is_origin_centric() and not self.inelastic_scattering):
      for h in indices:
        f_calc_linearisation.compute(h)
        assert f_calc_linearisation.f_calc.imag == 0
        assert flex.imag(f_calc_linearisation.grad_f_calc).all_eq(0)

    eta = 1e-8
    xs_forward = xs.deep_copy_scatterers()
    f_calc_linearisation_forward = (
      structure_factors.linearisation_of_f_calc_modulus_squared(xs_forward))

    deltas = flex.double()
    for direction in islice(self.structures_forward(xs, xs_forward, eta),
                            self.n_directions):
      for h in indices:
        f_calc_linearisation.compute(h)
        f_calc_linearisation_forward.compute(h)
        diff_num = (  f_calc_linearisation_forward.observable
                    - f_calc_linearisation.observable) / eta
        diff = f_calc_linearisation.grad_observable.dot(direction)
        delta = abs(1 - diff/diff_num)
        deltas.append(delta)
    stats = median_statistics(deltas)
    tol = 1e-3
    assert stats.median < tol, (str(space_group_info), stats.median)
    assert stats.median_absolute_deviation < tol, (str(space_group_info),
      stats.median_absolute_deviation)

class smtbx_against_cctbx_test_case(test_case):

  def exercise(self, space_group_info, verbose=False):
    xs = self.random_structure(space_group_info, set_grads=False)
    indices = self.miller_indices(space_group_info)
    cctbx_structure_factors = xray.structure_factors.from_scatterers_direct(
      xray_structure=xs,
      miller_set=miller.set(crystal.symmetry(unit_cell=xs.unit_cell(),
                                             space_group_info=space_group_info),
                                             indices))
    f_calc_linearisation = (
      structure_factors.linearisation_of_f_calc_modulus_squared(xs))
    for h, fc in cctbx_structure_factors.f_calc():
      f_calc_linearisation.compute(h)
      if fc == 0:
        assert f_calc_linearisation.f_calc == 0
      else:
        delta = abs((f_calc_linearisation.f_calc - fc)/fc)
        assert delta < 1e-6

def run(args):
  libtbx.utils.show_times_at_exit()
  parser = smtbx.development.space_group_option_parser()
  options = parser.process(args)

  t = smtbx_against_cctbx_test_case(inelastic_scattering=False)
  options.loop_over_space_groups(t.exercise)

  n_directions = 2
  t = consistency_test_cases(n_directions, inelastic_scattering=False)
  options.loop_over_space_groups(t.exercise)

  t = consistency_test_cases(n_directions, inelastic_scattering=True)
  options.loop_over_space_groups(t.exercise)

if __name__ == '__main__':
  import sys
  run(sys.argv[1:])

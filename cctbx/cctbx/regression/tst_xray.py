from cctbx.development import random_structure
from cctbx.development import debug_utils
from cctbx import xray
from cctbx import crystal
from cctbx import sgtbx
from cctbx import adptbx
import cctbx.eltbx.xray_scattering
from cctbx import eltbx
from cctbx.array_family import flex
from libtbx.test_utils import approx_equal
import pickle
from cStringIO import StringIO
import sys

def exercise_scatterer():
  assert xray.scatterer(scattering_type="Cval").element_symbol() == "C"
  assert xray.scatterer(scattering_type="si+4").element_symbol() == "Si"
  assert xray.scatterer(scattering_type="x").element_symbol() is None

def exercise_structure():
  cs = crystal.symmetry((5.01, 5.01, 5.47, 90, 90, 120), "P 62 2 2")
  sp = crystal.special_position_settings(cs)
  scatterers = flex.xray_scatterer((
    xray.scatterer("Si1", (1./2, 1./2, 0.3)),
    xray.scatterer("O1", (0.18700, -0.20700, 0.83333))))
  xs = xray.structure(sp, scatterers)
  assert xs.scatterers().size() == 2
  assert xs.n_undefined_multiplicities() == 0
  assert tuple(xs.special_position_indices()) == (0, 1)
  s = StringIO()
  xs.show_special_position_shifts(
    sites_cart_original=cs.unit_cell().orthogonalization_matrix()
                       *scatterers.extract_sites(),
    out=s,
    prefix="%^")
  assert s.getvalue() == """\
%^Number of sites in special positions: 2
%^  Minimum distance between symmetrically equivalent sites: 0.5
%^  Label   Mult   Shift    Fractional coordinates
%^  Si1       3    0.182 (  0.5000   0.5000   0.3000) original
%^        site sym 222   (  0.5000   0.5000   0.3333) exact
%^                               1/2,1/2,1/3
%^  O1        6    0.050 (  0.1870  -0.2070   0.8333) original
%^        site sym 2     (  0.1970  -0.1970   0.8333) exact
%^                        1/2*x-1/2*y,-1/2*x+1/2*y,5/6
"""
  ys = xs.deep_copy_scatterers()
  ys.add_scatterers(ys.scatterers())
  assert ys.scatterers().size() == 4
  assert xs.scatterers().size() == 2
  assert tuple(ys.special_position_indices()) == (0, 1, 2, 3)
  ys.add_scatterer(ys.scatterers()[0])
  assert ys.scatterers().size() == 5
  assert tuple(ys.special_position_indices()) == (0, 1, 2, 3, 4)
  sx = xs.primitive_setting()
  assert sx.unit_cell().is_similar_to(xs.unit_cell())
  assert str(sx.space_group_info()) == "P 62 2 2"
  sx = xs.change_hand()
  assert sx.unit_cell().is_similar_to(xs.unit_cell())
  assert str(sx.space_group_info()) == "P 64 2 2"
  assert approx_equal(sx.scatterers()[0].site, (-1./2, -1./2, -1./3))
  assert approx_equal(sx.scatterers()[1].site, (-0.19700, 0.19700, -0.833333))
  p1 = xs.asymmetric_unit_in_p1()
  assert p1.scatterers().size() == 2
  for i in xrange(2):
    assert p1.scatterers()[i].weight() == xs.scatterers()[i].weight()
  assert str(p1.space_group_info()) == "P 1"
  p1 = xs.expand_to_p1()
  assert p1.scatterers().size() == 9
  for i in xrange(2):
    assert p1.scatterers()[i].weight() != xs.scatterers()[i].weight()
  sh = p1.apply_shift((0.2,0.3,-1/6.))
  assert approx_equal(sh.scatterers()[0].site, (0.7,0.8,1/6.))
  assert approx_equal(sh.scatterers()[3].site, (0.3970,0.1030,2/3.))
  sl = sh[:1]
  assert sl.scatterers().size() == 1
  assert sl.scatterers()[0].label == sh.scatterers()[0].label
  sl = sh[1:4]
  assert sl.scatterers().size() == 3
  for i in xrange(3):
    assert sl.scatterers()[i].label == sh.scatterers()[i+1].label
  xs.scatterers().set_occupancies(flex.double((0.5,0.2)))
  s = xs.sort(by_value="occupancy")
  assert approx_equal(s.scatterers().extract_occupancies(), (0.2,0.5))
  assert s.scatterers()[0].label == "O1"
  assert s.scatterers()[1].label == "Si1"
  aw = xs.atomic_weights()
  assert approx_equal(aw, (28.086, 15.999))
  center_of_mass = xs.center_of_mass(atomic_weights=aw)
  assert approx_equal(center_of_mass, (1.335228, 1.071897, 2.815899))
  center_of_mass = xs.center_of_mass()
  assert approx_equal(center_of_mass, (1.335228, 1.071897, 2.815899))
  ys = xs.apply_shift(
    shift=xs.unit_cell().fractionalize([-e for e in center_of_mass]),
    recompute_site_symmetries=True)
  assert approx_equal(ys.center_of_mass(), (0,0,0))
  ys = xray.structure(xs)
  assert ys.atomic_weights().size() == 0
  ys = xray.structure(sp, scatterers)
  ys.scatterers()[1].occupancy = 0.5
  assert approx_equal(ys.scatterers()[1].weight(),0.25)
  ys.scatterers()[1].occupancy -= 0.1
  assert approx_equal(ys.scatterers()[1].weight(),0.2)
  assert xs.n_parameters(xray.structure_factors.gradient_flags(default=True)) \
         == 14
  g = flex.vec3_double(((0.1,0.2,0.3),(0.2,0.3,0.4)))
  xs.apply_special_position_ops_d_target_d_site(g)
  assert approx_equal(g[0], (0,0,0))
  assert approx_equal(g[1], (-0.05,0.05,0))
  xs.replace_scatterers(xs.scatterers()[:1], None)
  assert xs.scatterers().size() == 1
  assert tuple(xs.special_position_indices()) == (0,)
  sd = ys.scattering_dict(table="wk1995")
  assert sd.lookup("Si").gaussian.n_terms() == 5
  sd = ys.scattering_dict(table="it1992")
  assert sd.lookup("Si").gaussian.n_terms() == 4
  sd = ys.scattering_dict(custom_dict={"Si":eltbx.xray_scattering.gaussian(1)})
  assert sd.lookup("Si").gaussian.n_terms() == 0
  s = StringIO()
  sd.show_summary(f=s)
  assert s.getvalue().strip() == "Si:0+c*1 O:4+c*1"
  s = StringIO()
  sd.show(f=s)
  assert s.getvalue() == """\
Number of scattering types: 2
  Type Number   Weight   Gaussians
   O       1      8.00       4+c
   Si      1      1.00       0+c
"""
  s = StringIO()
  sd.show(f=s, show_weights=False)
  assert s.getvalue() == """\
Number of scattering types: 2
  Type Number   Gaussians
   O       1        4+c
   Si      1        0+c
"""
  s = StringIO()
  sd.show(f=s, show_gaussians=False)
  assert s.getvalue() == """\
Number of scattering types: 2
  Type Number   Weight
   O       1      8.00
   Si      1      1.00
"""
  s = StringIO()
  sd.show(f=s, show_weights=False, show_gaussians=False)
  assert s.getvalue() == """\
Number of scattering types: 2
  Type Number
   O       1
   Si      1
"""
  wd = sd.wilson_dict()
  assert len(wd) == 2
  assert wd['O'] == 1
  assert wd['Si'] == 1
  am = xs.asu_mappings(buffer_thickness=1)
  assert am.mappings().size() == xs.scatterers().size()
  rs = p1.random_shift_sites(max_shift_cart=0.2)
  assert flex.max(flex.abs(p1.difference_vectors_cart(rs).as_double())) <= 0.2
  assert approx_equal(p1.rms_difference(p1), 0)
  assert approx_equal(rs.rms_difference(rs), 0)
  assert p1.rms_difference(rs) > 0
  for s in [xs, ys, p1, rs]:
    p = pickle.dumps(s)
    l = pickle.loads(p)
    assert l.scatterers().size() == s.scatterers().size()
    assert l.special_position_indices().all_eq(s.special_position_indices())
  xs0 = xray.structure(
    crystal_symmetry=crystal.symmetry(
      unit_cell=(10,10,10,90,90,90),
      space_group_symbol="P 2 2 2"))
  xs0.add_scatterer(xray.scatterer(label="C", site=(0.1,0.1,0.1)))
  assert xs0.site_symmetry_table().get(0).is_point_group_1()
  xs1 = xs0.apply_shift(shift=(-0.08,-0.1,0), recompute_site_symmetries=False)
  assert xs1.site_symmetry_table().get(0).is_point_group_1()
  xs2 = xs0.apply_shift(shift=(-0.08,-0.1,0), recompute_site_symmetries=True)
  assert str(xs2.site_symmetry_table().get(0).special_op()) == "0,0,z"
  assert approx_equal(xs1.scatterers()[0].site, (0.02, 0, 0.1))
  assert approx_equal(xs2.scatterers()[0].site, (0, 0, 0.1))
  assert list(xs1.deep_copy_scatterers().special_position_indices()) == []
  assert list(xs2.deep_copy_scatterers().special_position_indices()) == [0]
  assert list(xs1[:].special_position_indices()) == []
  assert list(xs2[:].special_position_indices()) == [0]
  xs1.add_scatterer(xs1.scatterers()[0])
  assert list(xs1[:].special_position_indices()) == [1]
  xs1.add_scatterer(xs1.scatterers()[0], xs1.site_symmetry_table().get(0))
  assert list(xs1[:].special_position_indices()) == [1]
  xs1.add_scatterers(xs1.scatterers())
  assert list(xs1[:].special_position_indices()) == [1,3,4,5]
  xs1.add_scatterers(xs1.scatterers(), xs1.site_symmetry_table())
  assert list(xs1[:].special_position_indices()) == [1,3,4,5,7,9,10,11]
  for selection in [flex.size_t([1,4,6]),
                    flex.bool([False,True,False,False,True,False,
                               True,False,False,False,False,False])]:
    xs2 = xs1.select(selection=selection)
    assert xs2.scatterers().size() == 3
    assert list(xs2.special_position_indices()) == [0,1]
    if (isinstance(selection, flex.bool)):
      xs2 = xs1.select(selection=selection, negate=True)
      assert xs2.scatterers().size() == 9
  xs2 = xs1[2::2]
  assert xs2.scatterers().size() == 5
  assert list(xs2[:].special_position_indices()) == [1,4]
  xs1.replace_scatterers(xs2.scatterers(), None)
  assert list(xs1[:].special_position_indices()) == [0,1,2,3,4]
  xs1.replace_scatterers(xs2.scatterers(), xs2.site_symmetry_table())
  assert list(xs1[:].special_position_indices()) == [1,4]
  xs2 = xs1.asymmetric_unit_in_p1()
  assert xs2.unit_cell().is_similar_to(xs1.unit_cell())
  assert xs2.space_group().order_z() == 1
  assert list(xs2[:].special_position_indices()) == [1,4]
  for append_number_to_labels in [False, True]:
    xs2 = xs1.expand_to_p1(append_number_to_labels=append_number_to_labels)
    assert xs2.scatterers().size() == 16
    xs2 = xray.structure(xs1, xs1.scatterers())
    xs2 = xs2.expand_to_p1(append_number_to_labels=append_number_to_labels)
    assert xs2.scatterers().size() == 10
  cb_op = sgtbx.change_of_basis_op("z,x,y")
  xs2 = xs1.change_basis(cb_op)
  for i,sc in enumerate(xs2.scatterers()):
    assert sc.multiplicity() > 0
    ss = xs2.site_symmetry_table().get(i)
    assert ss.multiplicity() == sc.multiplicity()
    assert ss.multiplicity() * ss.n_matrices() == xs2.space_group().order_z()
  xs2 = xs2.expand_to_p1()
  for sc in xs2.scatterers():
    assert sc.multiplicity() == 1
  assert xs2.scatterers().size() == 16
  assert approx_equal(xs2.scatterers()[0].site, (0.1, 0.02, 0))
  assert approx_equal(xs2.scatterers()[4].site, (0.1, 0, 0))
  xs1.scatterers().set_occupancies(flex.random_double(size=5))
  xs2 = xs1.sort(by_value="occupancy")
  assert xs2.special_position_indices().size() == 2
  xs2.set_sites_frac(xs2.sites_frac()+(0.1,0.2,0.3))
  xs2.set_sites_cart(xs2.sites_cart()+(1,2,3))
  assert approx_equal(xs2.extract_u_iso_or_u_equiv(), [0,0,0,0,0])
  i = xs2.special_position_indices()[0]
  assert approx_equal(xs2.scatterers()[i].site, (0.2, 0.4, 0.7))
  assert list(xs2.is_positive_definite_u()) == [False]*5
  assert list(xs2.is_positive_definite_u(u_cart_tolerance=0)) == [True]*5
  xs2.tidy_us(u_min=1)
  assert approx_equal(xs2.scatterers().extract_u_iso(), [1]*5)
  xs2.shift_us(u_shift=2)
  assert approx_equal(xs2.scatterers().extract_u_iso(), [3]*5)
  xs2.shift_us(b_shift=-adptbx.u_as_b(2))
  assert approx_equal(xs2.scatterers().extract_u_iso(), [1]*5)
  xs2.apply_symmetry_sites()
  assert approx_equal(xs2.scatterers()[i].site, (0, 0, 0.7))
  xs2.apply_symmetry_u_stars()
  s = StringIO()
  xs1.show_distances(distance_cutoff=0.1, out=s)
  assert s.getvalue() == """\
C  pair count:   2       <<  0.0200,  0.0000,  0.1000>>
  C:   0.0000             (  0.0200,  0.0000,  0.1000)
  C:   0.0000             (  0.0200,  0.0000,  0.1000)
C  pair count:   1       <<  0.0000,  0.0000,  0.1000>>
  C:   0.0000             (  0.0000,  0.0000,  0.1000)
C  pair count:   2       <<  0.0200,  0.0000,  0.1000>>
  C:   0.0000             (  0.0200,  0.0000,  0.1000)
  C:   0.0000             (  0.0200,  0.0000,  0.1000)
C  pair count:   2       <<  0.0200,  0.0000,  0.1000>>
  C:   0.0000             (  0.0200,  0.0000,  0.1000)
  C:   0.0000             (  0.0200,  0.0000,  0.1000)
C  pair count:   1       <<  0.0000,  0.0000,  0.1000>>
  C:   0.0000             (  0.0000,  0.0000,  0.1000)
"""
  # exercise set_b_iso()
  cs = crystal.symmetry((5.01, 6.01, 5.47, 60, 80, 120), "P1")
  sp = crystal.special_position_settings(cs)
  scatterers = flex.xray_scatterer((
    xray.scatterer("C", (1./2, 1./2, 0.3)),
    xray.scatterer("C", (0.18700, -0.20700, 0.83333))))
  xs = xray.structure(sp, scatterers)
  b_iso_value = 25.0
  xs.set_b_iso(value = b_iso_value)
  result = flex.double([25,25])
  assert approx_equal(xs.scatterers().extract_u_iso()/adptbx.b_as_u(1), result)
  b_iso_values = flex.double([7,9])
  xs.set_b_iso(values = b_iso_values)
  assert approx_equal(xs.scatterers().extract_u_iso()/adptbx.b_as_u(1), b_iso_values)
  # exercise shake_b_iso()
  xs.shake_b_iso(deviation = 10)
  results = [[7.7,9.9],[7.7,8.1],[6.3,9.9],[6.3,8.1]]
  result = flex.to_list(xs.scatterers().extract_u_iso()/adptbx.b_as_u(1))
  assert result in results
  #
  xs.scatterers().set_u_iso(flex.double([0.1,0.2]))
  assert xs.scatterers().count_anisotropic() == 0
  xs.convert_to_anisotropic()
  assert xs.scatterers().count_anisotropic() == 2
  assert approx_equal(xs.scatterers().extract_u_cart(unit_cell=xs.unit_cell()),
    [[0.1]*3+[0]*3, [0.2]*3+[0]*3])
  xs.convert_to_isotropic()
  assert xs.scatterers().count_anisotropic() == 0
  assert approx_equal(xs.scatterers().extract_u_iso(), [0.1,0.2])
  ### shake_sites
  xs = random_structure.xray_structure(
                               space_group_info = sgtbx.space_group_info("P1"),
                               elements         = ["N"]*500,
                               unit_cell        = (10, 20, 30, 70, 80, 120))
  errors = [0.1,0.5,0.9,1.2,1.5,2.0,3.0]
  for error in errors:
    xs_shaked = xs.shake_sites(mean_error = error)
    sites_cart_xs        = xs.sites_cart()
    sites_cart_xs_shaked = xs_shaked.sites_cart()
    mean_err = flex.mean(flex.sqrt((sites_cart_xs - sites_cart_xs_shaked).dot()))
    #rmsd = sites_cart_xs.rms_difference(sites_cart_xs_shaked)
    #assert approx_equal(error, rmsd, 0.00005)
    assert approx_equal(error, mean_err, 0.00005)
  ### random remove sites
  for fraction in xrange(1, 99+1):
    fraction /= 100.
    selection = xs.random_remove_sites_selection(fraction = fraction)
    deleted = selection.count(False) / float(selection.size())
    retained= selection.count(True)  / float(selection.size())
    assert approx_equal(fraction, deleted)
    assert approx_equal(1-deleted, retained)

def exercise_u_base():
  d_min = 9
  grid_resolution_factor = 1/3.
  for quality_factor in (1,2,4,8,10,100,200,1000):
    u_base = xray.calc_u_base(d_min, grid_resolution_factor, quality_factor)
    assert approx_equal(
      quality_factor,
      xray.structure_factors.quality_factor_from_any(
        d_min=d_min,
        grid_resolution_factor=grid_resolution_factor,
        u_base=u_base))
    assert approx_equal(
      quality_factor,
      xray.structure_factors.quality_factor_from_any(
        d_min=d_min,
        grid_resolution_factor=grid_resolution_factor,
        b_base=adptbx.u_as_b(u_base)))
    assert approx_equal(
      quality_factor,
      xray.structure_factors.quality_factor_from_any(
        quality_factor=quality_factor))

def exercise_from_scatterers_direct(space_group_info,
                                    element_type,
                                    n_elements=3,
                                    volume_per_atom=1000,
                                    d_min=3,
                                    anomalous_flag=0,
                                    anisotropic_flag=0,
                                    verbose=0):
  structure = random_structure.xray_structure(
    space_group_info,
    elements=[element_type]*n_elements,
    volume_per_atom=volume_per_atom,
    min_distance=5,
    general_positions_only=True,
    random_f_prime_d_min=d_min-1,
    random_f_prime_scale=0.6,
    random_f_double_prime=anomalous_flag,
    anisotropic_flag=anisotropic_flag,
    random_u_iso=True,
    random_u_iso_scale=.3,
    random_u_cart_scale=.3,
    random_occupancy=True)
  if (0 or verbose):
    structure.show_summary().show_scatterers()
  f_obs_exact = structure.structure_factors(
    d_min=d_min, algorithm="direct",
    cos_sin_table=False).f_calc()
  assert f_obs_exact.anomalous_flag() == anomalous_flag
  f_obs_simple = xray.ext.structure_factors_simple(
    f_obs_exact.unit_cell(),
    f_obs_exact.space_group(),
    f_obs_exact.indices(),
    structure.scatterers(),
    structure.scattering_dict()).f_calc()
  if (0 or verbose):
    for i,h in enumerate(f_obs_exact.indices()):
      print h
      print f_obs_simple[i]
      print f_obs_exact.data()[i]
      if (abs(f_obs_simple[i]-f_obs_exact.data()[i]) >= 1.e-10):
        print "MISMATCH"
      print
  mismatch = flex.max(flex.abs(f_obs_exact.data() - f_obs_simple))
  assert mismatch < 1.e-10, mismatch
  f_obs_table = f_obs_exact.structure_factors_from_scatterers(
    xray_structure=structure,
    algorithm="direct",
    cos_sin_table=True).f_calc()
  ls = xray.targets_least_squares_residual(
    abs(f_obs_exact).data(), f_obs_table.data(), False, 1)
  if (0 or verbose):
    print "r-factor:", ls.target()
  assert ls.target() < 1.e-4

def exercise_f_obs_minus_xray_structure_f_calc(
      space_group_info,
      d_min=3,
      verbose=0):
  structure = random_structure.xray_structure(
    space_group_info,
    elements=["C"]*3,
    volume_per_atom=1000,
    min_distance=5,
    general_positions_only=True,
    random_u_iso=False)
  if (0 or verbose):
    structure.show_summary().show_scatterers()
  f_obs_exact = structure.structure_factors(
    d_min=d_min, algorithm="direct",
    cos_sin_table=False).f_calc()
  two_f_obs_minus_f_calc=abs(f_obs_exact).f_obs_minus_xray_structure_f_calc(
    f_obs_factor=2,
    xray_structure=structure,
    structure_factor_algorithm="direct",
    cos_sin_table=False)
  phase_error = two_f_obs_minus_f_calc.mean_weighted_phase_error(
    phase_source=f_obs_exact)
  if (0 or verbose):
    print "%.2f" % phase_error
  assert approx_equal(phase_error, 0)
  two_f_obs_minus_f_calc=abs(f_obs_exact).f_obs_minus_xray_structure_f_calc(
    f_obs_factor=2,
    xray_structure=structure[:-1],
    structure_factor_algorithm="direct",
    cos_sin_table=False)
  fft_map = two_f_obs_minus_f_calc.fft_map()
  fft_map.apply_sigma_scaling()
  real_map = fft_map.real_map_unpadded()
  density_at_sites = [real_map.eight_point_interpolation(scatterer.site)
    for scatterer in structure.scatterers()]
  try:
    assert min(density_at_sites[:-1]) > 7
    assert density_at_sites[-1] > 2.5
  except AssertionError:
    print "density_at_sites:", density_at_sites
    raise

def exercise_n_gaussian(space_group_info, verbose=0):
  structure_5g = random_structure.xray_structure(
    space_group_info,
    elements=["H", "C", "N", "O", "S"]*3)
  if (0 or verbose):
    structure_five.show_summary().show_scatterers()
  structure_4g = structure_5g.deep_copy_scatterers()
  structure_2g = structure_5g.deep_copy_scatterers()
  structure_5g.scattering_dict(table="wk1995")
  structure_4g.scattering_dict(table="it1992")
  structure_2g.scattering_dict(
    custom_dict=eltbx.xray_scattering.two_gaussian_agarwal_isaacs.table)
  for scatterer_group in structure_5g.scattering_dict().dict().values():
    assert scatterer_group.gaussian.n_terms() == 5
  for scatterer_group in structure_4g.scattering_dict().dict().values():
    assert scatterer_group.gaussian.n_terms() == 4
  for scatterer_group in structure_2g.scattering_dict().dict().values():
    assert scatterer_group.gaussian.n_terms() == 2
  d_min = 1
  f_calc_5g = structure_5g.structure_factors(
    d_min=d_min,
    algorithm="direct",
    cos_sin_table=False).f_calc()
  f_calc_4g = f_calc_5g.structure_factors_from_scatterers(
    xray_structure=structure_4g,
    algorithm="direct",
    cos_sin_table=False).f_calc()
  f_calc_2g = f_calc_5g.structure_factors_from_scatterers(
    xray_structure=structure_2g,
    algorithm="direct",
    cos_sin_table=False).f_calc()
  for n,f_calc_ng in ((4,f_calc_4g), (2,f_calc_2g)):
    ls = xray.targets_least_squares_residual(
      abs(f_calc_5g).data(), f_calc_ng.data(), False, 1)
    if (0 or verbose):
      print "%d-gaussian r-factor:" % n, ls.target()
    if (n == 2):
      assert ls.target() < 0.002
    else:
      assert ls.target() < 0.0002

def run_call_back(flags, space_group_info):
  if (1):
    for element_type in ("Se", "const"):
      for anomalous_flag in [0,1]:
        for anisotropic_flag in [0,1]:
          for with_shift in [0,1]:
            if (with_shift):
              sgi = debug_utils.random_origin_shift(space_group_info)
            else:
              sgi = space_group_info
            exercise_from_scatterers_direct(
              space_group_info=sgi,
              element_type=element_type,
              anomalous_flag=anomalous_flag,
              anisotropic_flag=anisotropic_flag,
              verbose=flags.Verbose)
  if (1):
    exercise_n_gaussian(
      space_group_info=space_group_info)
  if (1):
    exercise_f_obs_minus_xray_structure_f_calc(
      space_group_info=space_group_info)

def run():
  exercise_scatterer()
  exercise_structure()
  exercise_u_base()
  debug_utils.parse_options_loop_space_groups(sys.argv[1:], run_call_back)
  print "OK"

if (__name__ == "__main__"):
  run()

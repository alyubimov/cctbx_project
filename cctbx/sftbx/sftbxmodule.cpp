// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2001 Oct 22: Created (R.W. Grosse-Kunstleve)
 */

#include <boost/python/cross_module.hpp>
#include <cctbx/miller_bpl.h>
#include <cctbx/coordinates_bpl.h>
#include <cctbx/xray_scatterer.h>

namespace {

  using namespace cctbx;

  typedef sftbx::XrayScatterer<double, eltbx::CAASF_WK1995> ex_xray_scatterer;

  std::complex<double>
  py_StructureFactor_plain(const sgtbx::SpaceGroup& SgOps,
                           const Miller::Index& H,
                           const fractional<double>& X) {
    return sftbx::StructureFactor(SgOps, H, X);
  }
  std::complex<double>
  py_StructureFactor_iso(const sgtbx::SpaceGroup& SgOps,
                         const uctbx::UnitCell& UCell,
                         const Miller::Index& H,
                         const fractional<double>& X,
                         double Uiso) {
    return sftbx::StructureFactor(SgOps, UCell, H, X, Uiso);
  }
  std::complex<double>
  py_StructureFactor_aniso(const sgtbx::SpaceGroup& SgOps,
                           const Miller::Index& H,
                           const fractional<double>& X,
                           const af::double6& Ustar) {
    return sftbx::StructureFactor(SgOps, H, X, Ustar);
  }

  af::double3
  py_StructureFactor_dX(const sgtbx::SpaceGroup& SgOps,
                        const Miller::Index& H,
                        const fractional<double>& X,
                        const std::complex<double>& phase_indep_coeff,
                        const std::complex<double>& dTarget_dFcalc) {
    return sftbx::StructureFactor_dX(
      SgOps, H, X, phase_indep_coeff, dTarget_dFcalc);
  }

  void
  py_StructureFactorArray(
    const uctbx::UnitCell& UC,
    const sgtbx::SpaceGroup& SgOps,
    const af::shared<Miller::Index>& H,
    const af::shared<ex_xray_scatterer>& Sites,
    af::shared<std::complex<double> > Fcalc)
  {
    sftbx::StructureFactorArray(
      UC, SgOps, H.const_ref(), Sites.const_ref(),
      Fcalc.ref());
  }

  void
  py_StructureFactor_dX_Array(
    const uctbx::UnitCell& UC,
    const sgtbx::SpaceGroup& SgOps,
    const af::shared<Miller::Index>& H,
    const af::shared<std::complex<double> >& dTarget_dFcalc,
    const af::shared<ex_xray_scatterer>& Sites,
    af::shared<af::double3> dF_dX)
  {
    sftbx::StructureFactor_dX_Array(
      UC, SgOps, H.const_ref(), dTarget_dFcalc.const_ref(), Sites.const_ref(),
      dF_dX.ref());
  }

  af::shared<Miller::Index>
  py_BuildMillerIndices_Resolution_d_min(
    const uctbx::UnitCell& UC,
    const sgtbx::SpaceGroupInfo& SgInfo,
    double Resolution_d_min)
  {
    af::shared<Miller::Index> result;
    sgtbx::MillerIndexGenerator(
      UC, SgInfo, Resolution_d_min).AddToArray(result);
    return result;
  }
  af::shared<Miller::Index>
  py_BuildMillerIndices_MaxIndex(
    const sgtbx::SpaceGroupInfo& SgInfo,
    const Miller::Index& MaxIndex)
  {
    af::shared<Miller::Index> result;
    sgtbx::MillerIndexGenerator(
      SgInfo, MaxIndex).AddToArray(result);
    return result;
  }

#   include <cctbx/basic/from_bpl_import.h>

  void init_module(python::module_builder& this_module)
  {
    const std::string Revision = "$Revision$";
    this_module.add(ref(to_python(
        Revision.substr(11, Revision.size() - 11 - 2))), "__version__");

    python::import_converters<uctbx::UnitCell>
    py_UnitCell("cctbx_boost.uctbx", "UnitCell");
    python::import_converters<sgtbx::SpaceGroup>
    py_SpaceGroup("cctbx_boost.sgtbx", "SpaceGroup");
    python::import_converters<sgtbx::SpaceGroupInfo>
    py_SpaceGroupInfo("cctbx_boost.sgtbx", "SpaceGroupInfo");
    python::import_converters<eltbx::CAASF_WK1995>
    py_CAASF_WK1995("cctbx_boost.eltbx.caasf_wk1995", "CAASF_WK1995");

    python::import_converters<af::shared<std::complex<double> > >
    py_shared_complex_double(
      "cctbx_boost.arraytbx.shared", "complex_double");

    python::import_converters<af::shared<Miller::Index> >
    py_shared_Miller_Index(
      "cctbx_boost.arraytbx.shared", "Miller_Index");

    python::import_converters<af::shared<ex_xray_scatterer> >
    py_shared_XrayScatterer("cctbx_boost.arraytbx.shared", "XrayScatterer");

    python::import_converters<af::shared<af::double3> >
    py_shared_double3("cctbx_boost.arraytbx.shared", "double3");

    class_builder<ex_xray_scatterer>
    py_XrayScatterer(this_module, "XrayScatterer");
    python::export_converters(py_XrayScatterer);

    this_module.def(py_StructureFactor_plain, "StructureFactor");
    this_module.def(py_StructureFactor_iso,   "StructureFactor");
    this_module.def(py_StructureFactor_aniso, "StructureFactor");

    py_XrayScatterer.def(constructor<>());
    py_XrayScatterer.def(constructor<
      const std::string&,
      const eltbx::CAASF_WK1995&,
      const std::complex<double>&,
      const fractional<double>&,
      const double&,
      const double&>());
    py_XrayScatterer.def(constructor<
      const std::string&,
      const eltbx::CAASF_WK1995&,
      const std::complex<double>&,
      const fractional<double>&,
      const double&,
      const af::double6&>());
    py_XrayScatterer.def(
      &ex_xray_scatterer::Label, "Label");
    py_XrayScatterer.def(
      &ex_xray_scatterer::CAASF, "CAASF");
    py_XrayScatterer.def(
      &ex_xray_scatterer::fpfdp, "fpfdp");
    py_XrayScatterer.def(
      &ex_xray_scatterer::Coordinates, "Coordinates");
    py_XrayScatterer.def(
      &ex_xray_scatterer::Occ, "Occ");
    py_XrayScatterer.def(
      &ex_xray_scatterer::isAnisotropic, "isAnisotropic");
    py_XrayScatterer.def(
      &ex_xray_scatterer::Uiso, "Uiso");
    py_XrayScatterer.def(
      &ex_xray_scatterer::Uaniso, "Uaniso");
    py_XrayScatterer.def(
      &ex_xray_scatterer::M, "M");
    py_XrayScatterer.def(
      &ex_xray_scatterer::w, "w");
    py_XrayScatterer.def(
      &ex_xray_scatterer::ApplySymmetry, "ApplySymmetry");
    py_XrayScatterer.def(
      &ex_xray_scatterer::set_Coordinates, "set_Coordinates");
    py_XrayScatterer.def(
      &ex_xray_scatterer::StructureFactor, "StructureFactor");
    py_XrayScatterer.def(
      &ex_xray_scatterer::StructureFactor_dX, "StructureFactor_dX");

    this_module.def(py_StructureFactorArray, "StructureFactorArray");
    this_module.def(py_StructureFactor_dX_Array, "StructureFactor_dX_Array");

    this_module.def(py_BuildMillerIndices_Resolution_d_min,
                      "BuildMillerIndices");
    this_module.def(py_BuildMillerIndices_MaxIndex,
                      "BuildMillerIndices");
  }

}

BOOST_PYTHON_MODULE_INIT(sftbx)
{
  boost::python::module_builder this_module("sftbx");
  init_module(this_module);
}

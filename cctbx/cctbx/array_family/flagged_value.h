// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Jan 2002: Created (R.W. Grosse-Kunstleve)
 */

#ifndef CCTBX_ARRAY_FAMILY_FLAGGED_VALUE_H
#define CCTBX_ARRAY_FAMILY_FLAGGED_VALUE_H

namespace cctbx { namespace af {

  template <typename ValueType>
  struct flagged_value {
    typedef ValueType value_type;
    typedef bool tag_type;
    ValueType v;
    bool f;
    flagged_value() : f(false) {}
    flagged_value(const ValueType& val, bool flag = true) : v(val), f(flag) {}
    ValueType get(const ValueType& default_value = ValueType()) const {
      if (f) return v;
      return default_value;
    }
  };

}} // namespace cctbx::af

#include <cctbx/array_family/flagged_value_algebra.h>

namespace cctbx { namespace af {

  template<typename ValueTypeLhs, typename ValueTypeRhs>
  struct binary_operator_traits<
    flagged_value<ValueTypeLhs>,
    flagged_value<ValueTypeRhs> > {
    typedef binary_operator_traits<ValueTypeLhs, ValueTypeRhs> val_traits;
    typedef flagged_value<typename val_traits::arithmetic> arithmetic;
    typedef flagged_value<typename val_traits::logical> logical;
    typedef flagged_value<typename val_traits::boolean> boolean;
  };

}} // namespace cctbx::af

#endif // CCTBX_ARRAY_FAMILY_FLAGGED_VALUE_H

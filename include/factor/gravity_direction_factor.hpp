#ifndef IKALIBR_GRAVITY_DIRECTION_FACTOR_HPP
#define IKALIBR_GRAVITY_DIRECTION_FACTOR_HPP

#include "calib/estimator.h"
#include "util/utils_tpl.hpp"

namespace ns_ikalibr {

struct GravityDirectionFactor {
    EIGEN_MAKE_ALIGNED_OPERATOR_NEW

    GravityDirectionFactor(const Eigen::Vector3d &target_direction, double weight)
        : target_direction_(target_direction.normalized()), weight_(weight) {}

    static ceres::CostFunction *Create(const Eigen::Vector3d &target_direction, double weight) {
        // AutoDiffCostFunction<Class, num_residuals, parameter_block_sizes...>
        return new ceres::AutoDiffCostFunction<GravityDirectionFactor, 3, 3>(
            new GravityDirectionFactor(target_direction, weight));
    }

    template <typename T>
    bool operator()(const T *const gravity, T *residuals) const {
        Eigen::Map<const Eigen::Vector3<T>> g(gravity);
        Eigen::Map<Eigen::Vector3<T>> r(residuals);

        // Normalize the gravity vector
        Eigen::Vector3<T> g_normalized = g.normalized();
        
        // The residual is the difference between the normalized gravity vector and the target direction
        r = T(weight_) * (g_normalized - target_direction_.cast<T>());

        return true;
    }

private:
    Eigen::Vector3d target_direction_;
    double weight_;
};

} // namespace ns_ikalibr

#endif // IKALIBR_GRAVITY_DIRECTION_FACTOR_HPP
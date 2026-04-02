#ifndef IKALIBR_GRAVITY_UTILS_HPP
#define IKALIBR_GRAVITY_UTILS_HPP

#include "sophus/so3.hpp"
#include "Eigen/Core"

namespace ns_ikalibr {

/**
 * @brief Obtains a rotation that aligns the gravity vector with the configured direction
 * @param SO3_B0ToRef Initial rotation from body to reference frame
 * @param gravityInRef Gravity vector in reference frame
 * @param targetDir Target gravity direction to align with
 * @return Rotation that aligns gravity with configured direction
 */
inline Sophus::SO3d ObtainAlignedWtoRef(const Sophus::SO3d &SO3_B0ToRef,
                                       const Eigen::Vector3d &gravityInRef,
                                       const Eigen::Vector3d &targetDir) {
    // Get the current gravity direction in the reference frame
    Eigen::Vector3d currentDir = gravityInRef.normalized();

    // Compute the rotation axis and angle to align current direction with target direction
    Eigen::Vector3d rotDir = currentDir.cross(targetDir).normalized();
    double angRad = std::acos(currentDir.dot(targetDir));

    // Create rotation that aligns gravity with configured direction
    Sophus::SO3d SO3_WtoRef = 
        Sophus::SO3d(Eigen::AngleAxisd(angRad, rotDir).toRotationMatrix()) * SO3_B0ToRef;
    return SO3_WtoRef;
}

} // namespace ns_ikalibr

#endif // IKALIBR_GRAVITY_UTILS_HPP
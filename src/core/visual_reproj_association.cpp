// iKalibr: Unified Targetless Spatiotemporal Calibration Framework
// Copyright 2024, the School of Geodesy and Geomatics (SGG), Wuhan University, China
// https://github.com/Unsigned-Long/iKalibr.git
//
// Author: Shuolong Chen (shlchen@whu.edu.cn)
// GitHub: https://github.com/Unsigned-Long
//  ORCID: 0000-0002-5283-9057
//
// Purpose: See .h/.hpp file.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// * Redistributions of source code must retain the above copyright notice,
//   this list of conditions and the following disclaimer.
// * Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
// * The names of its contributors can not be
//   used to endorse or promote products derived from this software without
//   specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.

#include "core/visual_reproj_association.h"
#include "config/configor.h"
#include "factor/data_correspondence.h"
#include "spdlog/spdlog.h"
#include "veta/veta.h"

namespace {
bool IKALIBR_UNIQUE_NAME(_2_) = ns_ikalibr::_1_(__FILE__);
}

namespace ns_ikalibr {

VisualReProjAssociator::VisualReProjAssociator(const CameraModelType &type)
    : ExposureFactor(CameraModel::RSCameraExposureFactor(type)) {}

VisualReProjAssociator::Ptr VisualReProjAssociator::Create(const CameraModelType &type) {
    return std::make_shared<VisualReProjAssociator>(type);
}

std::vector<VisualReProjCorrSeq::Ptr> VisualReProjAssociator::Association(
    const ns_veta::Veta &veta, const ns_veta::PinholeIntrinsic::Ptr &intri) const {
    // scale weight from image pixel to real scale
    const double weight = intri->ImagePlaneToCameraPlaneError(1.0);

    const double maxSpan = Configor::Prior::MaxTemporalSpan;

    std::vector<VisualReProjCorrSeq::Ptr> corrVec;
    corrVec.reserve(veta.structure.size());
    std::size_t totalPairs = 0, skippedPairs = 0;

    for (const auto &[lmId, lm] : veta.structure) {
        auto begIter = lm.obs.cbegin();
        const auto &[viewIdFir, featFir] = *begIter;
        const auto &viewFir = veta.views.find(viewIdFir)->second;
        // RS line factor: use distorted pixel Y directly (features are already in distorted space)
        const double lFir =
            featFir.x(1) / static_cast<double>(viewFir->imgHeight) - ExposureFactor;

        auto corrSeq = std::make_shared<VisualReProjCorrSeq>();

        Eigen::Vector3d lmInFir = veta.poses.at(viewFir->poseId).Inverse().operator()(lm.X);
        corrSeq->invDepthFir = std::make_unique<double>(1.0 / lmInFir(2));
        corrSeq->lmId = lmId;
        corrSeq->corrs.reserve(lm.obs.size() - 1);
        corrSeq->firObvViewId = viewIdFir;
        corrSeq->firObv = featFir;

        for (auto curIter = std::next(begIter); curIter != lm.obs.cend(); ++curIter) {
            const auto &[viewIdCur, featCur] = *curIter;
            const auto &viewCur = veta.views.find(viewIdCur)->second;

            ++totalPairs;
            if (maxSpan > 0 &&
                std::abs(viewCur->timestamp - viewFir->timestamp) > maxSpan) {
                ++skippedPairs;
                continue;
            }

            const double lCur =
                featCur.x(1) / static_cast<double>(viewCur->imgHeight) - ExposureFactor;

            corrSeq->corrs.push_back(VisualReProjCorr::Create(
                viewFir->timestamp, viewCur->timestamp,
                featFir.x, featCur.x,
                lFir, lCur,
                weight));
        }
        if (!corrSeq->corrs.empty()) {
            corrVec.push_back(corrSeq);
        }
    }

    spdlog::info("[TEMPORAL_FILTER] MaxTemporalSpan={:.1f}s: kept {} pairs, "
                 "skipped {} ({:.0f}%), landmarks with pairs: {}",
                 maxSpan, totalPairs - skippedPairs, skippedPairs,
                 totalPairs > 0 ? 100.0 * skippedPairs / totalPairs : 0.0,
                 corrVec.size());

    return corrVec;
}
}  // namespace ns_ikalibr
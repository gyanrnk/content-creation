import { Composition } from "remotion";
import { GoalsEdit, FPS, TOTAL_FRAMES } from "./GoalsEdit";
import { LastDance, LD_FPS, LD_TOTAL } from "./LastDance";
import { UCLGoals, UCL_FPS, UCL_TOTAL } from "./UCLGoals";
import { GoldenBoot, GB_FPS, GB_TOTAL } from "./GoldenBoot";
import { Difference, DF_FPS, DF_TOTAL } from "./Difference";
import { UCLTop5, U5_FPS, U5_TOTAL } from "./UCLTop5";
import { EraBattle, EB_FPS, ebTotal, DEFAULT_ERA_PROPS } from "./EraBattle";
import { GuessPlayer, GP_FPS, GP_TOTAL, DEFAULT_GUESS_PROPS } from "./GuessPlayer";
import { WhatIf, WI_FPS, wiTotal, DEFAULT_WHATIF_PROPS } from "./WhatIf";
import { CleanSheet, CS_FPS, csTotal, DEFAULT_CS_PROPS } from "./CleanSheet";
import { Archive, AR_FPS, AR_TOTAL, DEFAULT_ARCHIVE_PROPS } from "./Archive";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="GoalsEdit"
        component={GoalsEdit}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="LastDance"
        component={LastDance}
        durationInFrames={LD_TOTAL}
        fps={LD_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="UCLGoals"
        component={UCLGoals}
        durationInFrames={UCL_TOTAL}
        fps={UCL_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="GoldenBoot"
        component={GoldenBoot}
        durationInFrames={GB_TOTAL}
        fps={GB_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="Difference"
        component={Difference}
        durationInFrames={DF_TOTAL}
        fps={DF_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="UCLTop5"
        component={UCLTop5}
        durationInFrames={U5_TOTAL}
        fps={U5_FPS}
        width={1080}
        height={1920}
      />
      {/* Data-driven: make_packs.py feeds this with --props, and the duration
          recalculates from however many duels the pack carries. */}
      <Composition
        id="EraBattle"
        component={EraBattle}
        durationInFrames={ebTotal(DEFAULT_ERA_PROPS.duels.length)}
        fps={EB_FPS}
        width={1080}
        height={1920}
        defaultProps={DEFAULT_ERA_PROPS}
        calculateMetadata={({ props }) => ({
          durationInFrames: ebTotal(props.duels?.length ?? 3),
        })}
      />
      <Composition
        id="GuessPlayer"
        component={GuessPlayer}
        durationInFrames={GP_TOTAL}
        fps={GP_FPS}
        width={1080}
        height={1920}
        defaultProps={DEFAULT_GUESS_PROPS}
      />
      <Composition
        id="WhatIf"
        component={WhatIf}
        durationInFrames={wiTotal(DEFAULT_WHATIF_PROPS.swaps.length)}
        fps={WI_FPS}
        width={1080}
        height={1920}
        defaultProps={DEFAULT_WHATIF_PROPS}
        calculateMetadata={({ props }) => ({
          durationInFrames: wiTotal(props.swaps?.length ?? 3),
        })}
      />
      <Composition
        id="CleanSheet"
        component={CleanSheet}
        durationInFrames={csTotal(DEFAULT_CS_PROPS.keepers.length)}
        fps={CS_FPS}
        width={1080}
        height={1920}
        defaultProps={DEFAULT_CS_PROPS}
        calculateMetadata={({ props }) => ({
          durationInFrames: csTotal(props.keepers?.length ?? 3),
        })}
      />
      <Composition
        id="Archive"
        component={Archive}
        durationInFrames={AR_TOTAL}
        fps={AR_FPS}
        width={1080}
        height={1920}
        defaultProps={DEFAULT_ARCHIVE_PROPS}
      />
    </>
  );
};

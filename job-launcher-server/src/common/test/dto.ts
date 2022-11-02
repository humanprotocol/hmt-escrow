import { v4 } from "uuid";
import { IJobCreateDto } from "../../job/interfaces";
import { IUserCreateDto } from "../../user/interfaces";

export const generateUserCreateDto = (data: Partial<IUserCreateDto> = {}): IUserCreateDto => {
  return Object.assign(
    {
      password: "human",
      confirm: "human",
      captcha: "HUMAN",
      email: `human+${v4()}@human.com`,
    },
    data,
  );
};

export const generateJobCreateDto = (data: Partial<IJobCreateDto> = {}): IJobCreateDto => {
  return Object.assign(
    {
      dataUrl: `https://human+${v4()}.json`,
      groundTruthFileUrl: `https://human+${v4()}.json`,
      annotationsPerImage: 10,
      labels: ['car', 'plain'],
      requesterDescription: `human+${v4()}`,
      requesterAccuracyTarget: 90,
      price: 10,
      fee: 0.1,
      transactionHash: v4()
    },
    data,
  );
};
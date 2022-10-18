export interface IUser {
  email?: string | null;
}

export interface IJobDetails {
  price: number;
  labels: Array<string>;
  dataUrl: string;
  networkId?: number;
  requestType?: string;
  datasetLength?: number;
  annotationsPerImage: number;
  requesterDescription: string;
  requesterAccuracyTarget: number;
  // requesterQuestion: string;
  // requesterQuestionExample: string;
}
export interface ITx {
  hash: string | null;
}
export interface IJob {
  details: IJobDetails;
  stepTwo: {
    mount: number;
  };
  tx: ITx;
}

export interface IGenericResponse {
  status: string;
  message: string;
}

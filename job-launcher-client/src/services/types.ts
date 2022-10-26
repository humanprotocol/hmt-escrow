export interface IUser {
  email?: string | null;
}

export interface IJobDetails {
  price: number;
  labels: Array<string>;
  dataUrl: string;
  annotationsPerImage: number;
  requesterDescription: string;
  requesterAccuracyTarget: number;
  networkId?: number;
  requestType?: string;
  datasetLength?: number;
}
export interface ITx {
  hash: string;
}
export interface IJob {
  details: IJobDetails;
  tx: ITx;
}

export interface IGenericResponse {
  status: string;
  message: string;
}

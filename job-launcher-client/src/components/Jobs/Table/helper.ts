import { PropName, ColumnTitle } from './columns';

export const getTitle = (prop: string) => {
  switch (prop) {
    case PropName.Status:
      return ColumnTitle.Status;
    case PropName.Id:
      return ColumnTitle.Id;
    case PropName.NetworkId:
      return ColumnTitle.NetworkId;
    case PropName.DataUrl:
      return ColumnTitle.DataUrl;
    case PropName.Data:
      return ColumnTitle.Data;
    case PropName.ManifestHash:
      return ColumnTitle.ManifestHash;
    case PropName.DatasetLength:
      return ColumnTitle.DatasetLength;
    case PropName.AnnotationsPerImage:
      return ColumnTitle.AnnotationsPerImage;
    case PropName.Labels:
      return ColumnTitle.Labels;
    case PropName.RequesterAccuracyTarget:
      return ColumnTitle.RequesterAccuracyTarget;
    case PropName.TokenAddress:
      return ColumnTitle.TokenAddress;
    case PropName.Price:
      return ColumnTitle.Price;
    case PropName.Mode:
      return ColumnTitle.Mode;
    case PropName.RequestType:
      return ColumnTitle.RequestType;
    case PropName.Created:
      return ColumnTitle.Created;
    case PropName.Updated:
      return ColumnTitle.Updated;
    case PropName.RequesterDescription:
      return ColumnTitle.RequesterDescription;
    case PropName.RecordingOracleAddress:
      return ColumnTitle.RecordingOracleAddress;
    case PropName.UserId:
      return ColumnTitle.UserId;
    case PropName.RecordingOracleUrl:
      return ColumnTitle.RecordingOracleUrl;
    case PropName.ReputationOracleUrl:
      return ColumnTitle.ReputationOracleUrl;
    case PropName.ExchangeOracleUrl:
      return ColumnTitle.ExchangeOracleUrl;
    case PropName.RecordingOracleStake:
      return ColumnTitle.RecordingOracleStake;
    case PropName.ReputationOracleAddress:
      return ColumnTitle.ReputationOracleAddress;
    case PropName.ExchangeOracleAddress:
      return ColumnTitle.ExchangeOracleAddress;
    case PropName.ReputationOracleStake:
      return ColumnTitle.ReputationOracleStake;
    case PropName.EscrowAddress:
      return ColumnTitle.EscrowAddress;
    case PropName.Fee:
      return ColumnTitle.Fee;
    // case PropName.Mode:
    //   return ColumnTitle.Mode;
    // case PropName.RequesterQuestion:
    //   return ColumnTitle.RequesterQuestion;
    // case PropName.RequesterQuestionExample:
    //   return ColumnTitle.RequesterQuestionExample;
    default:
      return prop;
  }
};

export const dateFormat = (date: any) => {
  return new Date(date).toLocaleDateString('en-us', {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

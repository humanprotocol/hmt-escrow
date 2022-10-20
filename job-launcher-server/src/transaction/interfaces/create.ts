import { TransactionStatus, TransactionType } from "../../common/decorators";

export interface ITransactionCreateDto {
  amount: number;
  hash: string;
  type: TransactionType;
  status: TransactionStatus;
}

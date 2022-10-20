import { TransactionStatus } from "../../common/decorators";
import { ITransactionCommonDto } from "../../common/dto/transaction-common";

export interface ITransactionUpdateDto extends ITransactionCommonDto {
  status?: TransactionStatus;
}

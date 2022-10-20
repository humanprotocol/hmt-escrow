import { ApiPropertyOptional } from "@nestjs/swagger";
import { IsEnum } from "class-validator";
import { TransactionStatus } from "../../common/decorators";
import { TransactionCommonDto } from "../../common/dto";
import { ITransactionUpdateDto } from "../interfaces";

export class UpdateTransactionDto extends TransactionCommonDto implements ITransactionUpdateDto {
  @ApiPropertyOptional({
    enum: TransactionStatus,
  })
  @IsEnum(TransactionStatus)
  public status: TransactionStatus;
}

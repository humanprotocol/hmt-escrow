import { Column, Entity, ManyToOne } from "typeorm";

import { NS } from "../common/constants";
import { BaseEntity } from "../database/base.entity";
import { ITransaction, TransactionStatus, TransactionType } from "../common/decorators";
import { JobEntity } from "../job/job.entity";

@Entity({ schema: NS, name: "transaction" })
export class TransactionEntity extends BaseEntity implements ITransaction {
  @Column({ type: "decimal" })
  public amount: number;

  @Column({ type: "varchar" })
  public hash: string;

  @Column({ type: "int" })
  public confirmations: number;

  @Column({ type: "enum", enum: TransactionType })
  public type: TransactionType;

  @Column({
    type: "enum",
    enum: TransactionStatus,
  })
  public status: TransactionStatus;

  @ManyToOne(() => JobEntity, job => job.transactions)
  public job: JobEntity;

  @Column({ type: "int" })
  public jobId: number;
}

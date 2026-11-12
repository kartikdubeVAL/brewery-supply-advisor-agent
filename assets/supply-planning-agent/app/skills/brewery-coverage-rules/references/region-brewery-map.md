# Region to Brewery Mapping

| Region | Brewery Name | Brewery Code Prefix | Tank ID Prefix Examples |
|--------|-------------|---------------------|------------------------|
| South  | Munich      | MUC                 | MUC-T001, MUC-T002     |
| South  | Nuremberg   | NUE                 | NUE-T001, NUE-T006     |
| West   | Dortmund    | DOR                 | DOR-T001, DOR-T002     |
| East   | Leipzig     | LEI                 | LEI-T001, LEI-T002     |

## Rules

- South region demand can ONLY be covered by Munich or Nuremberg tanks.
- West region demand can ONLY be covered by Dortmund tanks.
- East region demand can ONLY be covered by Leipzig tanks.
- Cross-regional supply is never allowed under any circumstances.

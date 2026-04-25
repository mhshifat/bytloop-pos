import { apiFetch } from "./fetcher";

export type Department = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly parentId: string | null;
};

export type DepartmentNode = Department & {
  readonly children: readonly DepartmentNode[];
};

export type ProductDepartment = {
  readonly productId: string;
  readonly departmentId: string;
};

export type ProductDepartmentDetail = {
  readonly productId: string;
  readonly departmentId: string;
  readonly departmentCode: string;
  readonly departmentName: string;
};

export async function getProductDepartment(
  productId: string,
): Promise<ProductDepartmentDetail> {
  return apiFetch<ProductDepartmentDetail>(`/departments/products/${productId}`);
}

export type DepartmentSalesRow = {
  readonly departmentId: string;
  readonly name: string;
  readonly revenueCents: number;
  readonly unitCount: number;
};

export async function listDepartmentsTree(): Promise<readonly DepartmentNode[]> {
  return apiFetch<readonly DepartmentNode[]>("/departments");
}

export async function createDepartment(input: {
  readonly code: string;
  readonly name: string;
  readonly parentId?: string | null;
}): Promise<Department> {
  return apiFetch<Department>("/departments", {
    method: "POST",
    json: {
      code: input.code,
      name: input.name,
      parentId: input.parentId ?? null,
    },
  });
}

export async function assignProductToDepartment(input: {
  readonly productId: string;
  readonly departmentId: string;
}): Promise<ProductDepartment> {
  return apiFetch<ProductDepartment>("/departments/assign", {
    method: "POST",
    json: input,
  });
}

export async function salesByDepartment(params: {
  readonly since: string;
  readonly until: string;
}): Promise<readonly DepartmentSalesRow[]> {
  const sp = new URLSearchParams();
  sp.set("since", params.since);
  sp.set("until", params.until);
  return apiFetch<readonly DepartmentSalesRow[]>(
    `/departments/reports/sales?${sp.toString()}`,
  );
}

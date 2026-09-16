import * as utils from 'xlsx';
import * as path from 'path';
import * as fs from 'fs';

export interface ExcelOrderRow {
  "Order Ref"?: string;
  "Customer Name": string;
  "Phone Number": string;
  "City": string;
  "Address": string;
  "COD Amount": number | string;
  "Item Name"?: string;
  "Quantity"?: number | string;
  "Notes"?: string;
}

export class ExcelGenerator {
  private static ensureDirExists(dirPath: string) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  /**
   * Generates an Excel buffer or saves it to disk
   */
  public static createExcelBuffer(rows: ExcelOrderRow[]): Buffer {
    const worksheet = utils.utils.json_to_sheet(rows);
    const workbook = utils.utils.book_new();
    utils.utils.book_append_sheet(workbook, worksheet, "Orders");
    return utils.write(workbook, { type: "buffer", bookType: "xlsx" });
  }

  public static createExcelFile(rows: ExcelOrderRow[], fileName: string): string {
    const outputDir = path.resolve(__dirname, '../../test-data');
    this.ensureDirExists(outputDir);
    const filePath = path.join(outputDir, fileName);

    const worksheet = utils.utils.json_to_sheet(rows);
    const workbook = utils.utils.book_new();
    utils.utils.book_append_sheet(workbook, worksheet, "Orders");
    utils.writeFile(workbook, filePath);
    return filePath;
  }

  // --- Scenario 1: Valid Single Order ---
  public static getValidSingleOrderRows(): ExcelOrderRow[] {
    return [
      {
        "Order Ref": `EXCEL-VALID-${Date.now()}`,
        "Customer Name": "Mohamed Ali",
        "Phone Number": "+972598847044",
        "City": "Ramallah",
        "Address": "Main Plaza, Tower 3",
        "COD Amount": 199.99,
        "Item Name": "Premium Wireless Charger",
        "Quantity": 1,
        "Notes": "Valid single excel order case"
      }
    ];
  }

  // --- Scenario 2: Multi-Order Batch ---
  public static getMultiOrderBatchRows(): ExcelOrderRow[] {
    return [
      {
        "Order Ref": `EXCEL-BATCH-1-${Date.now()}`,
        "Customer Name": "Fatimah Al-Zahrani",
        "Phone Number": "0598847044",
        "City": "Nablus",
        "Address": "Rafidia St, Bldg 12",
        "COD Amount": 350.00,
        "Item Name": "Bluetooth Speaker",
        "Quantity": 2,
        "Notes": "Batch item 1"
      },
      {
        "Order Ref": `EXCEL-BATCH-2-${Date.now()}`,
        "Customer Name": "Tariq Mansour",
        "Phone Number": "+972598847044",
        "City": "Hebron",
        "Address": "Ein Sara St",
        "COD Amount": 75.50,
        "Item Name": "USB-C Fast Cable",
        "Quantity": 3,
        "Notes": "Batch item 2"
      }
    ];
  }

  // --- Scenario 3: Edge Cases (Arabic text, localized formats, spaces) ---
  public static getEdgeCaseRows(): ExcelOrderRow[] {
    return [
      {
        "Order Ref": `EXCEL-EDGE-${Date.now()}`,
        "Customer Name": "عبد الله محمد العتيبي", // Arabic Name
        "Phone Number": "+972 59 884 7044",       // Phone with intro +972 and spaces
        "City": "رام الله",                       // Arabic City
        "Address": "شارع الإرسال - عمارة الأمل",  // Arabic address
        "COD Amount": "0",                         // 0 COD / Prepaid
        "Item Name": "حافظة هاتف فاخرة",          // Arabic item name
        "Quantity": 1,
        "Notes": "اختبار الشحنات باللغة العربية"
      }
    ];
  }

  // --- Scenario 4: Invalid Rows (Validation errors verification) ---
  public static getInvalidRows(): ExcelOrderRow[] {
    return [
      {
        "Order Ref": `EXCEL-INVALID-1-${Date.now()}`,
        "Customer Name": "",                      // Missing Name (Invalid)
        "Phone Number": "12345",                  // Short/Invalid Phone
        "City": "",                               // Missing City
        "Address": "Unknown St",
        "COD Amount": -50.00,                     // Invalid negative COD
        "Item Name": "Test Item",
        "Quantity": 0,
        "Notes": "Invalid row for Django error testing"
      }
    ];
  }
}

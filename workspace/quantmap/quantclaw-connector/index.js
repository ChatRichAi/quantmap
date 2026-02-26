/**
 * QuantClaw Connector
 * 连接QuantClaw基因池到QuantMap
 */

const sqlite3 = require('sqlite3');
const { QEPProtocol } = require('../src/qep/protocol');
const path = require('path');

class QuantClawConnector {
  constructor(quantclawDbPath = '../quantclaw/evolution_hub.db') {
    this.dbPath = quantclawDbPath;
    this.qep = new QEPProtocol();
  }

  /**
   * 从QuantClaw导入基因到QuantMap
   */
  async importFromQuantClaw() {
    console.log('[Connector] Importing genes from QuantClaw...');
    
    const db = new sqlite3.Database(this.dbPath);
    
    return new Promise((resolve, reject) => {
      db.all('SELECT * FROM genes', [], (err, rows) => {
        if (err) {
          reject(err);
          return;
        }
        
        let imported = 0;
        
        for (const row of rows) {
          const gene = {
            id: row.gene_id,
            name: row.name,
            formula: row.formula,
            parameters: JSON.parse(row.parameters),
            generation: row.generation,
            parent_ids: row.parent_gene_id ? row.parent_gene_id.split('+') : [],
            source: 'quantclaw_import',
            created_at: row.created_at
          };
          
          this.qep.storeGene(gene);
          imported++;
        }
        
        console.log(`[Connector] Imported ${imported} genes`);
        resolve(imported);
      });
      
      db.close();
    });
  }

  /**
   * 将QuantMap验证结果导回QuantClaw
   */
  async exportValidationResults() {
    console.log('[Connector] Exporting validation results...');
    
    // 实现结果导出逻辑
    // 将回测验证结果写回QuantClaw数据库
  }
}

module.exports = { QuantClawConnector };

// CLI
if (require.main === module) {
  const connector = new QuantClawConnector();
  connector.importFromQuantClaw().catch(console.error);
}

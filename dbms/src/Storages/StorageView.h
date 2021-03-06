#pragma once

#include <Parsers/ASTSelectQuery.h>
#include <Parsers/IAST_fwd.h>
#include <Storages/IStorage.h>

#include <ext/shared_ptr_helper.h>


namespace DB
{

class StorageView : public ext::shared_ptr_helper<StorageView>, public IStorage
{
    friend struct ext::shared_ptr_helper<StorageView>;
public:
    std::string getName() const override { return "View"; }
    std::string getTableName() const override { return table_name; }
    std::string getDatabaseName() const override { return database_name; }

    /// It is passed inside the query and solved at its level.
    bool supportsSampling() const override { return true; }
    bool supportsFinal() const override { return true; }

    BlockInputStreams read(
        const Names & column_names,
        const SelectQueryInfo & query_info,
        const Context & context,
        QueryProcessingStage::Enum processed_stage,
        size_t max_block_size,
        unsigned num_streams) override;

    void rename(const String & /*new_path_to_db*/, const String & new_database_name, const String & new_table_name, TableStructureWriteLockHolder &) override
    {
        table_name = new_table_name;
        database_name = new_database_name;
    }

private:
    String table_name;
    String database_name;
    ASTPtr inner_query;

    void replaceTableNameWithSubquery(ASTSelectQuery * select_query, ASTPtr & subquery);

protected:
    StorageView(
        const String & database_name_,
        const String & table_name_,
        const ASTCreateQuery & query,
        const ColumnsDescription & columns_);
};

}

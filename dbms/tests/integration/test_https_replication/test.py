import time
import pytest

from helpers.cluster import ClickHouseCluster

from helpers.test_tools import assert_eq_with_retry

"""
Both ssl_conf.xml and no_ssl_conf.xml have the same port
"""

def _fill_nodes(nodes, shard):
    for node in nodes:
        node.query(
        '''
            CREATE DATABASE test;

            CREATE TABLE test_table(date Date, id UInt32, dummy UInt32)
            ENGINE = ReplicatedMergeTree('/clickhouse/tables/test{shard}/replicated', '{replica}', date, id, 8192);
        '''.format(shard=shard, replica=node.name))

cluster = ClickHouseCluster(__file__)
node1 = cluster.add_instance('node1', config_dir="configs", main_configs=['configs/remote_servers.xml', 'configs/ssl_conf.xml'], with_zookeeper=True)
node2 = cluster.add_instance('node2', config_dir="configs", main_configs=['configs/remote_servers.xml', 'configs/ssl_conf.xml'], with_zookeeper=True)

@pytest.fixture(scope="module")
def both_https_cluster():
    try:
        cluster.start()

        _fill_nodes([node1, node2], 1)

        yield cluster

    finally:
        cluster.shutdown()

def test_both_https(both_https_cluster):
    node1.query("insert into test_table values ('2017-06-16', 111, 0)")

    assert_eq_with_retry(node1, "SELECT id FROM test_table order by id", '111')
    assert_eq_with_retry(node2, "SELECT id FROM test_table order by id", '111')

    node2.query("insert into test_table values ('2017-06-17', 222, 1)")

    assert_eq_with_retry(node1, "SELECT id FROM test_table order by id", '111\n222')
    assert_eq_with_retry(node2, "SELECT id FROM test_table order by id", '111\n222')

node3 = cluster.add_instance('node3', config_dir="configs", main_configs=['configs/remote_servers.xml', 'configs/no_ssl_conf.xml'], with_zookeeper=True)
node4 = cluster.add_instance('node4', config_dir="configs", main_configs=['configs/remote_servers.xml', 'configs/no_ssl_conf.xml'], with_zookeeper=True)

@pytest.fixture(scope="module")
def both_http_cluster():
    try:
        cluster.start()

        _fill_nodes([node3, node4], 2)

        yield cluster

    finally:
        cluster.shutdown()

def test_both_http(both_http_cluster):
    node3.query("insert into test_table values ('2017-06-16', 111, 0)")

    assert_eq_with_retry(node3, "SELECT id FROM test_table order by id", '111')
    assert_eq_with_retry(node4, "SELECT id FROM test_table order by id", '111')

    node4.query("insert into test_table values ('2017-06-17', 222, 1)")

    assert_eq_with_retry(node3, "SELECT id FROM test_table order by id", '111\n222')
    assert_eq_with_retry(node4, "SELECT id FROM test_table order by id", '111\n222')

node5 = cluster.add_instance('node5', config_dir="configs", main_configs=['configs/remote_servers.xml', 'configs/ssl_conf.xml'], with_zookeeper=True)
node6 = cluster.add_instance('node6', config_dir="configs", main_configs=['configs/remote_servers.xml', 'configs/no_ssl_conf.xml'], with_zookeeper=True)

@pytest.fixture(scope="module")
def mixed_protocol_cluster():
    try:
        cluster.start()

        _fill_nodes([node5, node6], 3)

        yield cluster

    finally:
        cluster.shutdown()

def test_mixed_protocol(mixed_protocol_cluster):
    node5.query("insert into test_table values ('2017-06-16', 111, 0)")

    assert_eq_with_retry(node5, "SELECT id FROM test_table order by id", '111')
    assert_eq_with_retry(node6, "SELECT id FROM test_table order by id", '')

    node6.query("insert into test_table values ('2017-06-17', 222, 1)")

    assert_eq_with_retry(node5, "SELECT id FROM test_table order by id", '111')
    assert_eq_with_retry(node6, "SELECT id FROM test_table order by id", '222')

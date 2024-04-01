jQuery(document).ready(function($) {
    function fetchData() {
        $.ajax({
            url: ajaxObj.ajaxUrl,
            type: 'POST',
            data: {
                'action': 'get_filtered_data'
            },
            success: function(response) {
                if (response.success) {
                    // assets 데이터 처리
                    if (response.data.assets.length === 0) {
                        $('#assets-display').html('<p>No filtered assets available.</p>');
                    } else {
                        let assetsHtml = '<h3>Assets</h3><table><thead><tr><th>Asset</th><th>Margin Balance</th></tr></thead><tbody>';
                        response.data.assets.forEach(function(asset) {
                            assetsHtml += `<tr><td>${asset.asset}</td><td>${asset.marginBalance}</td></tr>`;
                        });
                        assetsHtml += '</tbody></table>';
                        $('#assets-display').html(assetsHtml);
                    }

                    // positions 데이터 처리
                    if (response.data.positions.length === 0) {
                        $('#positions-display').html('<p>No filtered positions available.</p>');
                    } else {
                        let positionsHtml = '<h3>Positions</h3><table><thead><tr><th>Symbol</th><th>PositionAmt</th><th>PositionType</th><th>EntryPrice</th><th>UnrealizedProfit</th><th>Leverage</th></tr></thead><tbody>';
                        response.data.positions.forEach(function(position) {
                            let positionType = parseFloat(position.positionAmt) > 0 ? "Long" : (parseFloat(position.positionAmt) < 0 ? "Short" : "Flat");
                            positionsHtml += `<tr><td>${position.symbol}</td><td>${position.positionAmt}</td><td>${positionType}</td><td>${position.entryPrice}</td><td>${position.unrealizedProfit}</td><td>${position.leverage}</td></tr>`;
                        });
                        positionsHtml += '</tbody></table>';
                        $('#positions-display').html(positionsHtml);
                    }

                    // daily_pnl 데이터 처리
                    if (response.data.daily_pnl && response.data.daily_pnl.length > 0) {
                        // 테이블 헤더를 추가
                        let dailyPnlHtml = '<h3>Daily PNL</h3><table><thead><tr><th>Total PNL</th></tr></thead><tbody>';
                        // 첫 번째 daily_pnl 항목의 PNL 값으로 행을 추가
                        dailyPnlHtml += `<tr><td>${response.data.daily_pnl[0].total_pnl}</td></tr>`;
                        dailyPnlHtml += '</tbody></table>';
                        // HTML 페이지에 테이블 표시
                        $('#pnl-display').html(dailyPnlHtml);
                    } else {
                        $('#pnl-display').html('<p>No Daily PNL data available.</p>');
                    }

                    // position_table 데이터 처리
                    if (response.data.positions_table.length === 0) {
                        $('#positions-table-display').html('<p>No position table data available.</p>');
                    } else {
                        let positionsTableHtml = '<h3>Buy/Sell Record</h3><table><thead><tr><th>Symbol</th><th>Buying Price</th><th>Selling Price</th><th>Realized PNL</th></tr></thead><tbody>';
                        response.data.positions_table.forEach(function(position) {
                            positionsTableHtml += `<tr><td>${position.symbol}</td><td>${position.price_before_last}</td><td>${position.last_price}</td><td>${position.realizedPnl}</td></tr>`;
                        });
                        positionsTableHtml += '</tbody></table>';
                        $('#positions-table-display').html(positionsTableHtml);
                    }
                } else {
                    console.error('Error fetching data');
                }
            },
            error: function(xhr, status, error) {
                console.error('AJAX Error:', status, error);
            }
        });
    }

    // 최초 실행 및 10초마다 데이터 새로고침
    fetchData();
    setInterval(fetchData, 1000); //1000 : 1초
});
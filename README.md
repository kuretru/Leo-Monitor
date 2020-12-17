# Leo-Monitor

【开发中】狮子监控

## 通信协议

<table>
<thead>
  <tr>
    <th colspan="2">报文起始符</th>
    <th>报文类型</th>
    <th>Payload长度(byte)</th>
    <th>Pyaload</th>
    <th>······</th>
    <th>Pyaload</th>
    <th>校验码</th>
    <th colspan="3">报文终止符</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>0xFF</td>
    <td>0xFF</td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td>0xFE</td>
    <td>0xEF</td>
    <td>\n</td>
  </tr>
</tbody>
</table>

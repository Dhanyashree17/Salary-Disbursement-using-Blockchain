// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SalaryDisbursement {
    address public owner;
    
    struct Employee {
        address walletAddress;
        uint256 salary;
        bool isActive;
    }
    
    mapping(address => Employee) public employees;
    address[] public employeeAddresses;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }

    function addEmployee(address _walletAddress, uint256 _salary) public onlyOwner {
        Employee memory newEmployee = Employee({
            walletAddress: _walletAddress,
            salary: _salary,
            isActive: true
        });
        employees[_walletAddress] = newEmployee;
        employeeAddresses.push(_walletAddress);
    }

    function removeEmployee(address _walletAddress) public onlyOwner {
        require(employees[_walletAddress].isActive, "Employee does not exist");
        employees[_walletAddress].isActive = false;
    }

    function paySalaries() public onlyOwner {
        for (uint256 i = 0; i < employeeAddresses.length; i++) {
            address employeeAddress = employeeAddresses[i];
            if (employees[employeeAddress].isActive) {
                payable(employeeAddress).transfer(employees[employeeAddress].salary);
            }
        }
    }

    // Function to receive Ether. msg.data must be empty
    receive() external payable {}

    // Fallback function is called when msg.data is not empty
    fallback() external payable {}
}


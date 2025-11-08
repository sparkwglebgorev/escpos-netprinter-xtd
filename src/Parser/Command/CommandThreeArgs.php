<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\EscposCommand;

class CommandThreeArgs extends EscposCommand
{
    private ?int $arg1 = null;
    private ?int $arg2 = null;
    private ?int $arg3 = null;

    public function addChar($char)
    {
        if ($this -> arg1 === null) {
            $this -> arg1 = ord($char);
            return true;
        } elseif ($this -> arg2 === null) {
            $this -> arg2 = ord($char);
            return true;
        } elseif ($this -> arg3 === null) {
            $this -> arg3 = ord($char);
            return true;
        }
        return false;
    }

    protected function getArg1(): ?int
    {
        return $this -> arg1;
    }

    protected function getArg2(): ?int
    {
        return $this -> arg2;
    }

    protected function getArg3(): ?int
    {
        return $this -> arg3;
    }
}
